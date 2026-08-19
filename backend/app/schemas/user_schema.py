"""
schemas/user_schema.py
=======================
Mô tả:
    Pydantic schemas kiểm soát dữ liệu vào/ra API cho User.
    Đây là "cổng kiểm tra" — FastAPI tự động validate và serialize.

Tại sao phân biệt Model vs Schema?
    Model (models/user.py)  = cấu trúc trong DB — có hashed_password
    Schema (schemas/)       = cấu trúc API    — KHÔNG CÓ hashed_password

    Quy tắc bảo mật: KHÔNG BAO GIỜ trả hashed_password ra ngoài API response!

Giao tiếp với:
    - routers/auth.py     : dùng RegisterRequest làm request body
    - services/auth_service.py : dùng để validate input
    - routers/auth.py     : dùng UserResponse làm response body

Design Pattern:
    DTO (Data Transfer Object) — tách biệt internal representation và external API.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


# INPUT SCHEMAS (Request) — Dữ liệu CLIENT gửi LÊN server
class RegisterRequest(BaseModel):
    """
    Schema cho POST /auth/register.

    Pydantic tự động:
    - Validate kiểu dữ liệu (nếu email sai format → 422 Unprocessable Entity)
    - Parse JSON body từ request
    - Tạo OpenAPI docs tự động

    Tại sao dùng EmailStr thay vì str?
    - EmailStr validate format email (phải có @, domain hợp lệ, v.v.)
    - Không cần tự viết regex validate email
    """
    email: EmailStr = Field(
        ...,                              # "..." nghĩa là required (bắt buộc)
        description="Email của người dùng, dùng làm tên đăng nhập",
        examples=["student@university.edu.vn"]
    )
    password: str = Field(
        ...,
        min_length=8,                     # Tối thiểu 8 ký tự — bảo mật cơ bản
        max_length=100,
        description="Mật khẩu (tối thiểu 8 ký tự)",
        examples=["SecurePass123!"]
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Tên đầy đủ của người dùng",
        examples=["Trần Thị Lan"]
    )

    @field_validator("full_name")
    @classmethod
    def full_name_must_not_be_blank(cls, v: str) -> str:
        """
        Validator tùy chỉnh: tên không được chỉ có dấu cách.
        Pydantic validators chạy sau khi type check, trước khi lưu DB.
        """
        if not v.strip():
            raise ValueError("Tên không được để trống")
        return v.strip()


class LoginRequest(BaseModel):
    """
    Schema cho POST /auth/login.

    Lưu ý: Không dùng OAuth2PasswordRequestForm của FastAPI vì:
    - OAuth2PasswordRequestForm yêu cầu form data (không phải JSON)
    - Chúng ta muốn JSON để đồng nhất với các endpoints khác
    - Đơn giản hơn cho frontend gọi API
    """
    email: EmailStr = Field(
        ...,
        description="Email đã đăng ký",
        examples=["student@university.edu.vn"]
    )
    password: str = Field(
        ...,
        description="Mật khẩu",
        examples=["SecurePass123!"]
    )


# ============================================================
# OUTPUT SCHEMAS (Response) — Dữ liệu server trả VỀ client
# ============================================================

class UserResponse(BaseModel):
    """
    Schema cho thông tin User được trả về trong API response.

    QUAN TRỌNG: KHÔNG có trường 'hashed_password'!
    Đây là lý do chính để tách Model và Schema.

    Tại sao có trường 'id' (string) thay vì '_id' (ObjectId)?
    - MongoDB lưu _id là ObjectId (binary format)
    - JSON không serialize được ObjectId
    - Phải convert sang string trước khi trả về
    - Dùng alias '_id' → 'id' để frontend dễ dùng hơn
    """
    id: str = Field(
        description="ID duy nhất của user (MongoDB ObjectId dạng string)"
    )
    email: str = Field(description="Email đăng nhập")
    full_name: str = Field(description="Tên đầy đủ")
    role: UserRole = Field(description="Vai trò trong hệ thống")
    is_active: bool = Field(description="Tài khoản có đang hoạt động không")
    created_at: datetime = Field(description="Thời gian tạo tài khoản")

    model_config = {
        # from_attributes=True: cho phép tạo schema từ dict (MongoDB document)
        "from_attributes": True,
        # json_schema_extra: thêm ví dụ vào OpenAPI docs
        "json_schema_extra": {
            "example": {
                "id": "64f1a2b3c4d5e6f7a8b9c0d1",
                "email": "student@university.edu.vn",
                "full_name": "Trần Thị Lan",
                "role": "member",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    }


class TokenResponse(BaseModel):
    """
    Schema cho response của POST /auth/login.
    Trả về JWT access token để client dùng cho các request tiếp theo.

    Tại sao token_type = "bearer"?
    - Đây là HTTP Authorization standard (RFC 6750)
    - Client gửi: "Authorization: Bearer <token>"
    - "bearer" nghĩa là "ai cầm token này thì có quyền đó"
    """
    access_token: str = Field(description="JWT token để xác thực các request tiếp theo")
    token_type: str = Field(default="bearer", description="Loại token (luôn là 'bearer')")
    expires_in: int = Field(description="Thời gian hết hạn (giây)")
    user: UserResponse = Field(description="Thông tin user đăng nhập")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900,
                "user": {
                    "id": "64f1a2b3c4d5e6f7a8b9c0d1",
                    "email": "student@university.edu.vn",
                    "full_name": "Trần Thị Lan",
                    "role": "member",
                    "is_active": True,
                    "created_at": "2024-01-15T10:30:00Z"
                }
            }
        }
    }


class TokenRefreshResponse(BaseModel):
    """
    Schema cho response của POST /auth/refresh.
    Trả về JWT access token mới.
    """
    access_token: str = Field(description="JWT token mới để xác thực các request tiếp theo")
    token_type: str = Field(default="bearer", description="Loại token (luôn là 'bearer')")
    expires_in: int = Field(description="Thời gian hết hạn của token mới (giây)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900
            }
        }
    }


class MessageResponse(BaseModel):
    """
    Schema generic cho các response chỉ trả về thông báo.
    Dùng cho: logout, delete, v.v.
    """
    message: str = Field(description="Thông báo kết quả")
    success: bool = Field(default=True, description="True nếu thành công")

