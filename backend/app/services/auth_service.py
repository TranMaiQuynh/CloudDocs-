"""
services/auth_service.py
========================
Mô tả:
    Business Logic Layer cho Authentication.
    Đây là "bộ não" xử lý các nghiệp vụ đăng ký và đăng nhập.

Tại sao cần Service Layer?
    Router chỉ nên làm:
        - Nhận HTTP request
        - Gọi Service
        - Trả HTTP response

    Service làm:
        - Kiểm tra điều kiện nghiệp vụ (email đã tồn tại chưa?)
        - Gọi Repository để lấy/lưu data
        - Gọi Security để hash/verify password, tạo token
        - Raise exception nếu có lỗi nghiệp vụ

    Ưu điểm:
        - Router "mỏng" (thin router) → dễ đọc, dễ test
        - Service có thể tái dùng (nhiều router cùng gọi 1 service)
        - Test service mà không cần HTTP context

Giao tiếp với:
    - repositories/user_repository.py : query MongoDB
    - core/security.py                : bcrypt, JWT
    - routers/auth.py                 : gọi service từ router
"""

from typing import Optional
from fastapi import HTTPException, status
# pyrefly: ignore [missing-import]
from pymongo.errors import DuplicateKeyError
from app.repositories import user_repository
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.models.user import UserRole
from app.schemas.user_schema import RegisterRequest, LoginRequest


async def register_user(request: RegisterRequest) -> dict:
    """
    Xử lý nghiệp vụ đăng ký tài khoản mới.

    Luồng chi tiết:
    1. Kiểm tra email đã tồn tại chưa (trước khi hash → tiết kiệm tài nguyên)
    2. Hash password bằng bcrypt
    3. Lưu user vào MongoDB
    4. Trả về user data (không có hashed_password)

    Tại sao raise HTTPException ở đây thay vì trong router?
    - HTTPException là FastAPI-specific, nhưng service cũng có thể raise nó
    - Alternative: raise custom exception rồi router catch và convert
    - Cho dự án này: raise trực tiếp đơn giản hơn và đủ tốt

    Tại sao check email trước khi hash?
    - bcrypt.hash() tốn ~100ms (chủ đích để chậm lại)
    - Nếu check sau khi hash → lãng phí 100ms mỗi request với email trùng
    - Còn một lý do bảo mật: tránh timing attack (dù ít liên quan ở đây)

    Args:
        request: RegisterRequest schema với email, password, full_name

    Returns:
        dict: {"user": {...}, "message": "..."}

    Raises:
        HTTPException 409: Email đã được sử dụng
        HTTPException 500: Lỗi server không mong đợi
    """

    # BƯỚC 1: Kiểm tra email đã tồn tại chưa
    existing_user = await user_repository.find_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email này đã được đăng ký. Vui lòng dùng email khác hoặc đăng nhập."
        )

    # BƯỚC 2: Hash password
    # Tuyệt đối không lưu plain_password — chỉ lưu hash
    hashed = hash_password(request.password)

    # BƯỚC 3: Lưu user vào MongoDB
    try:
        new_user = await user_repository.create_user(
            email=request.email,
            hashed_password=hashed,
            full_name=request.full_name,
            role=UserRole.MEMBER,  # Mặc định tất cả user mới đều là MEMBER
        )
    except DuplicateKeyError:
        # Race condition: 2 request cùng lúc với cùng email
        # Check ở bước 1 không đủ vì có khoảng thời gian giữa check và insert
        # MongoDB unique index sẽ catch trường hợp này
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email này đã được đăng ký. Vui lòng dùng email khác."
        )

    # BƯỚC 4: Format và trả về (không có hashed_password)
    formatted_user = user_repository.format_user_id(new_user)
    # Xóa hashed_password trước khi trả về — QUAN TRỌNG
    formatted_user.pop("hashed_password", None)

    return {
        "user": formatted_user,
        "message": "Đăng ký tài khoản thành công!"
    }


async def login_user(request: LoginRequest) -> dict:
    """
    Xử lý nghiệp vụ đăng nhập.

    Luồng chi tiết:
    1. Tìm user theo email
    2. Kiểm tra password có đúng không
    3. Kiểm tra tài khoản có active không
    4. Tạo JWT access token
    5. Trả về token + user info

    Bảo mật quan trọng — Generic Error Message:
    Khi email sai HOẶC password sai, đều trả về cùng 1 thông báo lỗi:
    "Email hoặc mật khẩu không đúng"

    Tại sao không phân biệt "Email không tồn tại" vs "Mật khẩu sai"?
    - Tránh "user enumeration attack": attacker biết được email nào đã đăng ký
    - Nếu trả về "Email không tồn tại" → attacker biết email đó chưa dùng
      → có thể dùng để spam, phishing, brute force có chủ đích

    Args:
        request: LoginRequest schema với email, password

    Returns:
        dict: {"access_token": "...", "token_type": "bearer", "expires_in": ..., "user": {...}}

    Raises:
        HTTPException 401: Email hoặc mật khẩu không đúng
        HTTPException 403: Tài khoản bị khóa
    """

    # BƯỚC 1: Tìm user theo email
    user = await user_repository.find_by_email(request.email)

    # BƯỚC 2: Kiểm tra user tồn tại VÀ password đúng
    # Lưu ý: kiểm tra cả 2 điều kiện với cùng thông báo lỗi (generic error)
    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng",
            headers={"WWW-Authenticate": "Bearer"},
            # WWW-Authenticate header: HTTP standard cho 401, báo client dùng Bearer token
        )

    # BƯỚC 3: Kiểm tra tài khoản có active không
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản của bạn đã bị khóa. Vui lòng liên hệ Admin."
        )

    # BƯỚC 4: Tạo cả Access Token và Refresh Token
    user_id = str(user["_id"])  # Convert ObjectId → string
    access_token = create_access_token(
        user_id=user_id,
        role=user["role"],
        email=user["email"],
    )
    refresh_token = create_refresh_token(user_id=user_id)

    # BƯỚC 5: Format response
    formatted_user = user_repository.format_user_id(user)
    formatted_user.pop("hashed_password", None)  # Xóa hash trước khi trả về

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert phút → giây
        "user": formatted_user,
    }


async def get_user_by_id(user_id: str) -> Optional[dict]:
    """
    Lấy thông tin user theo ID (dùng cho /auth/me endpoint).

    Args:
        user_id: MongoDB ObjectId dạng string

    Returns:
        dict | None: User info (không có hashed_password), None nếu không tìm thấy
    """
    user = await user_repository.find_by_id(user_id)
    if not user:
        return None

    formatted = user_repository.format_user_id(user)
    formatted.pop("hashed_password", None)
    return formatted


async def refresh_access_token(refresh_token: str) -> dict:
    """
    Xử lý nghiệp vụ đổi Refresh Token lấy Access Token mới.

    Args:
        refresh_token: Token dài hạn trích xuất từ HTTP-Only Cookie

    Returns:
        dict: {"access_token": "...", "token_type": "bearer", "expires_in": ...}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # BƯỚC 1: Decode refresh token
    payload = decode_access_token(refresh_token)
    if not payload:
        raise credentials_exception

    # BƯỚC 2: Kiểm tra loại token có phải refresh token không
    if payload.get("type") != "refresh":
        raise credentials_exception

    # BƯỚC 3: Lấy user_id và kiểm tra user có tồn tại và còn hoạt động không
    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    user = await user_repository.find_by_id(user_id)
    if not user or not user.get("is_active", True):
        raise credentials_exception

    # BƯỚC 4: Tạo Access Token mới
    new_access_token = create_access_token(
        user_id=user_id,
        role=user["role"],
        email=user["email"],
    )

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }

