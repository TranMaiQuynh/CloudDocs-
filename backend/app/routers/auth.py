"""
routers/auth.py
================
Mô tả:
    API Layer cho Authentication — định nghĩa HTTP endpoints.

    Endpoints trong file này:
    POST /auth/register  → Đăng ký tài khoản mới
    POST /auth/login     → Đăng nhập, nhận JWT token
    POST /auth/logout    → Đăng xuất (client-side)
    GET  /auth/me        → Lấy thông tin user đang đăng nhập

Triết lý "Thin Router":
    Router chỉ làm:
    1. Định nghĩa HTTP method + path
    2. Khai báo request body schema (FastAPI validate tự động)
    3. Gọi Service
    4. Trả response với đúng HTTP status code

    Router KHÔNG làm:
    - Business logic (kiểm tra email trùng → Service làm)
    - Query database trực tiếp (→ Repository làm)
    - Hash password (→ Security làm)

Giao tiếp với:
    - schemas/user_schema.py  : dùng làm request/response type
    - services/auth_service   : delegate business logic
    - dependencies/auth_deps  : inject current_user cho /me endpoint
    - main.py                 : register router này vào app

HTTP Status Codes (best practices):
    201 Created    : Resource mới được tạo thành công (register)
    200 OK         : Request thành công (login, logout, me)
    401 Unauthorized: Chưa xác thực
    403 Forbidden  : Đã xác thực nhưng không có quyền
    409 Conflict   : Email đã tồn tại
    422 Unprocessable Entity: Validation error (FastAPI tự handle)
"""

from typing import Optional
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, status, Response, Cookie, HTTPException
from app.schemas.user_schema import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    TokenRefreshResponse,
    UserResponse,
    MessageResponse,
)
from app.services import auth_service
from app.dependencies.auth_deps import get_current_user
from app.core.config import settings

# APIRouter thay vì FastAPI instance
# Lý do: modular — nhiều router được gộp vào 1 FastAPI app trong main.py
# prefix="/auth": mọi endpoint trong router này đều bắt đầu bằng /auth
# tags=["Authentication"]: nhóm endpoints trong Swagger UI
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản mới",
    description="""
    Tạo tài khoản người dùng mới trong hệ thống.
    
    **Lưu ý:**
    - Email phải chưa được đăng ký
    - Mật khẩu tối thiểu 8 ký tự
    - Tài khoản mới luôn có role 'member'
    - Admin có thể upgrade role sau khi đăng ký
    """,
)
async def register(request: RegisterRequest):
    """
    Đăng ký tài khoản mới.

    FastAPI tự động:
    - Parse JSON body → RegisterRequest (validate email, min_length password)
    - Nếu validation fail → 422 Unprocessable Entity với chi tiết lỗi
    - Nếu validation pass → gọi hàm này với request đã validate

    Luồng: Router → auth_service.register_user() → Repository → MongoDB
    """
    result = await auth_service.register_user(request)
    return {
        "message": result["message"],
        "user": result["user"],
        "success": True,
    }


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Đăng nhập",
    description="""
    Đăng nhập bằng email và mật khẩu. Trả về JWT access token.
    
    **Sử dụng token:**
    Thêm vào header của mọi request sau khi login:
    ```
    Authorization: Bearer <access_token>
    ```
    """,
)
async def login(request: LoginRequest, response: Response):
    """
    Đăng nhập và nhận JWT token.

    response_model=TokenResponse:
    - FastAPI sẽ validate response với TokenResponse schema
    - Tự động serialize datetime, enum, v.v.
    - Ẩn các fields không có trong schema (bảo mật)
    """
    result = await auth_service.login_user(request)
    
    # Trích xuất refresh_token để lưu vào cookie bảo mật
    refresh_token = result.pop("refresh_token")
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Đặt thành True trong môi trường production (HTTPS)
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    )
    
    return result


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Đăng xuất",
    description="""
    Đăng xuất khỏi hệ thống.
    
    **Quan trọng - JWT Logout:**
    JWT là stateless — server không lưu danh sách token.
    Logout thực sự được thực hiện ở **phía client** bằng cách xóa token.
    
    Server chỉ xác nhận yêu cầu logout hợp lệ.
    
    **Client phải:**
    1. Xóa token khỏi localStorage/sessionStorage/cookie
    2. Redirect về trang login
    3. Không gửi token đó nữa
    """,
)
async def logout(response: Response, current_user: dict = Depends(get_current_user)):
    """
    Đăng xuất (server-side acknowledgment).

    Tại sao cần Depends(get_current_user) cho logout?
    - Verify token hợp lệ trước khi "logout" → tránh abuse
    - Log hoạt động logout (audit trail)
    - User phải đang đăng nhập mới logout được (common sense)
    """
    # Xóa Cookie refresh_token
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        samesite="lax"
    )
    return {
        "message": f"Đăng xuất thành công. Hẹn gặp lại, {current_user['full_name']}!",
        "success": True,
    }


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy thông tin tài khoản hiện tại",
    description="Trả về thông tin của user đang đăng nhập dựa trên JWT token.",
)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Lấy thông tin user đang đăng nhập.

    Endpoint này thường được frontend dùng khi:
    - App khởi động → kiểm tra token còn hợp lệ không
    - Hiển thị "Xin chào, [tên user]" trên header
    - Kiểm tra role để show/hide menu items

    Depends(get_current_user): FastAPI tự gọi auth check,
    nếu token invalid → 401 trước khi vào hàm này.
    """
    return current_user


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy Access Token mới",
    description="""
    Đổi Refresh Token trong HTTP-Only Cookie lấy Access Token mới.
    """,
)
async def refresh(refresh_token: Optional[str] = Cookie(None)):
    """
    Đổi Refresh Token lấy Access Token mới.

    FastAPI tự động trích xuất cookie 'refresh_token' từ request.
    Nếu không tìm thấy hoặc hết hạn -> trả về 401.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Không tìm thấy session làm mới. Vui lòng đăng nhập lại.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await auth_service.refresh_access_token(refresh_token)
    return result

