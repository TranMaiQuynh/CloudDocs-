"""
dependencies/auth_deps.py
==========================
Mô tả:
    FastAPI Dependency Injection cho Authentication & Authorization.
    Đây là "người gác cổng" — kiểm tra mọi request vào protected endpoints.

Tại sao dùng Dependency Injection (DI)?
    Không có DI:
        @router.get("/documents")
        async def get_docs(token: str = Header(...)):
            payload = decode_access_token(token)  # lặp lại mọi endpoint!
            if not payload: raise HTTPException(401)
            user = await find_by_id(payload["sub"])  # lặp lại!
            if user["role"] != "admin": raise HTTPException(403)  # lặp lại!
            ...

    Với DI:
        @router.get("/documents")
        async def get_docs(current_user = Depends(get_current_user)):
            # FastAPI tự gọi get_current_user, inject kết quả vào
            # Nếu token invalid → FastAPI tự raise 401 trước khi vào hàm này
            ...

    Ưu điểm DI:
    - DRY: không lặp lại auth logic
    - Composable: kết hợp dependencies (auth + role check)
    - Testable: inject mock user trong test
    - Clean: router tập trung vào business logic

Giao tiếp với:
    - core/security.py            : gọi decode_access_token()
    - repositories/user_repository: tìm user trong DB để verify vẫn active
    - routers/*.py                : dùng Depends(get_current_user) trong endpoint params
"""

from typing import Callable
# pyrefly: ignore [missing-import]
from fastapi import Depends, HTTPException, status
# pyrefly: ignore [missing-import]
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_access_token
from app.repositories import user_repository


"""
HTTPBearer: FastAPI built-in security scheme.
- Tự động extract token từ header "Authorization: Bearer <token>"
- Nếu header không có → 403 Forbidden (auto_error=True mặc định)
- Tích hợp với OpenAPI/Swagger UI: hiện nút "Authorize" để test

Tại sao dùng HTTPBearer thay vì tự parse header?
- Chuẩn hóa: theo RFC 6750 Bearer Token standard
- Swagger UI hiểu được → test API dễ hơn
- Validate format "Bearer <token>" tự động
"""
bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    Dependency: Xác thực request và trả về current user.

    FastAPI tự động:
    1. Gọi HTTPBearer để extract token từ Authorization header
    2. Gọi hàm này với credentials
    3. Inject kết quả vào tham số endpoint có Depends(get_current_user)

    Luồng:
    1. Decode JWT → lấy payload
    2. Check payload hợp lệ (có "sub" field)
    3. Query DB để verify user vẫn tồn tại và active
       (Tại sao query DB dù đã có info trong token?
        Token có thể hết hạn sau role change hoặc account bị khóa.
        DB query đảm bảo real-time status. Trade-off: thêm ~1-2ms latency)
    4. Return user dict cho endpoint

    Args:
        credentials: Chứa token từ "Authorization: Bearer <token>" header

    Returns:
        dict: User document (không có hashed_password)

    Raises:
        HTTPException 401: Token invalid hoặc user không tồn tại
    """
    # Thông báo lỗi generic — không tiết lộ chi tiết (security best practice)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực. Vui lòng đăng nhập lại.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # BƯỚC 1: Decode JWT
    token = credentials.credentials  # Lấy raw token string (không bao gồm "Bearer ")
    payload = decode_access_token(token)

    if payload is None:
        # Token invalid hoặc expired
        raise credentials_exception

    # BƯỚC 2: Lấy user_id từ payload
    user_id: str = payload.get("sub")
    if user_id is None:
        # Token không có "sub" field → malformed token
        raise credentials_exception

    # BƯỚC 3: Verify user vẫn tồn tại trong DB và còn active
    user = await user_repository.find_by_id(user_id)
    if user is None or not user.get("is_active", True):
        raise credentials_exception

    # BƯỚC 4: Format và return (loại bỏ hashed_password)
    formatted_user = user_repository.format_user_id(user)
    formatted_user.pop("hashed_password", None)
    return formatted_user


def require_role(*allowed_roles: str) -> Callable:
    """
    Dependency Factory: tạo dependency kiểm tra role của user.

    Đây là "Higher-Order Function" — hàm trả về hàm.

    Cách dùng:
        @router.delete("/documents/{id}")
        async def delete_doc(
            current_user = Depends(require_role("admin", "leader"))
        ):
            # Chỉ admin hoặc leader mới vào được đây
            ...

    Tại sao dùng factory thay vì viết từng dependency riêng?
        # Không dùng factory → phải viết:
        async def require_admin(user = Depends(get_current_user)):
            if user["role"] != "admin": raise 403

        async def require_admin_or_leader(user = Depends(get_current_user)):
            if user["role"] not in ["admin", "leader"]: raise 403

        # Dùng factory → chỉ cần 1 hàm linh hoạt:
        Depends(require_role("admin"))
        Depends(require_role("admin", "leader"))
        Depends(require_role("admin", "leader", "member"))

    Args:
        *allowed_roles: Các role được phép (variadic args)
                        Ví dụ: require_role("admin", "leader")

    Returns:
        Callable: Async function dùng làm FastAPI dependency
    """
    async def role_checker(
        current_user: dict = Depends(get_current_user)
    ) -> dict:
        """
        Inner function được FastAPI inject vào endpoint.
        current_user đã được authenticate bởi get_current_user.
        Giờ chỉ cần check role.
        """
        user_role = current_user.get("role")

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Bạn không có quyền thực hiện hành động này. "
                       f"Yêu cầu role: {', '.join(allowed_roles)}. "
                       f"Role của bạn: {user_role}."
            )

        return current_user

    return role_checker


# ============================================================
# PRE-BUILT DEPENDENCIES — Để tiện dùng trong các router
# ============================================================

# Chỉ cần authenticate (bất kỳ role nào)
# Dùng: Depends(authenticated)
authenticated = get_current_user

# Chỉ Admin
# Dùng: Depends(require_admin)
require_admin = require_role("admin")

# Admin hoặc Leader
# Dùng: Depends(require_admin_or_leader)
require_admin_or_leader = require_role("admin", "leader")

# Bất kỳ role nào (giống authenticated nhưng tường minh hơn)
# Dùng: Depends(require_any_role)
require_any_role = require_role("admin", "leader", "member")
