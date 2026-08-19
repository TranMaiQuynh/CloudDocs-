"""
schemas/permission_schema.py
============================
Mô tả:
    Pydantic schemas quản trị dữ liệu đầu vào/đầu ra cho phân quyền chia sẻ (Permissions).
"""

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from app.models.permission import AccessLevel


class PermissionCreateRequest(BaseModel):
    """
    Schema cho POST /permissions.
    Chia sẻ tài nguyên (tài liệu/thư mục) cho một cộng tác viên qua Email hoặc Nhóm học tập.
    """
    resource_id: str = Field(..., description="ID của thư mục hoặc tài liệu cần chia sẻ")
    resource_type: str = Field(..., description="Loại tài nguyên ('document' hoặc 'folder')")
    user_email: Optional[EmailStr] = Field(default=None, description="Email của người nhận quyền chia sẻ (nếu chia sẻ cho cá nhân)")
    group_id: Optional[str] = Field(default=None, description="ID của nhóm học tập nhận quyền (nếu chia sẻ cho nhóm)")
    share_type: str = Field(default="user", description="Hình thức chia sẻ: 'user' hoặc 'group'")
    access_level: AccessLevel = Field(
        default=AccessLevel.VIEWER,
        description="Cấp độ quyền chia sẻ: 'viewer' (chỉ đọc) hoặc 'editor' (có quyền sửa)"
    )

    @field_validator("resource_type")
    @classmethod
    def validate_resource_type(cls, v: str) -> str:
        val = v.strip().lower()
        if val not in ["document", "folder"]:
            raise ValueError("Loại tài nguyên phải là 'document' hoặc 'folder'")
        return val


class PermissionUpdateRequest(BaseModel):
    """
    Schema cho PATCH /permissions/{permission_id}.
    Cập nhật lại cấp độ quyền của một cộng tác viên.
    """
    access_level: AccessLevel = Field(..., description="Cấp độ quyền mới: 'viewer' hoặc 'editor'")


class PermissionResponse(BaseModel):
    """
    Schema phản hồi chi tiết về phân quyền.
    """
    id: str = Field(description="ID bản ghi phân quyền")
    resource_id: str = Field(description="ID tài nguyên chia sẻ")
    resource_type: str = Field(description="Loại tài nguyên ('document'/'folder')")
    user_id: str = Field(description="ID người nhận quyền hoặc nhóm nhận quyền")
    user_email: Optional[str] = Field(default=None, description="Email người nhận quyền (nếu là user)")
    group_name: Optional[str] = Field(default=None, description="Tên nhóm học tập nhận quyền (nếu là group)")
    share_type: str = Field(default="user", description="Hình thức chia sẻ: user hoặc group")
    access_level: str = Field(description="Cấp độ quyền: viewer/editor")
    granted_by: str = Field(description="ID người thực hiện chia sẻ")
    created_at: datetime = Field(description="Thời gian chia sẻ")
    updated_at: datetime = Field(description="Thời gian cập nhật")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "64f3d5e6f7a8b9c0d1e2f3a4",
                "resource_id": "64f2b3c4d5e6f7a8b9c0d1e2",
                "resource_type": "folder",
                "user_id": "64f1a2b3c4d5e6f7a8b9c0d1",
                "user_email": "lan@university.edu.vn",
                "share_type": "user",
                "access_level": "viewer",
                "granted_by": "64f1a2b3c4d5e6f7a8b9c0d9",
                "created_at": "2026-08-15T12:00:00Z",
                "updated_at": "2026-08-15T12:00:00Z"
            }
        }
    }


class LinkSharingResponse(BaseModel):
    """
    Schema phản hồi cấu hình chia sẻ qua link.
    """
    share_link_access: str = Field(..., description="Chế độ chia sẻ: 'restricted' hoặc 'anyone'")
    share_link_level: str = Field(..., description="Quyền hạn qua link: 'viewer' hoặc 'editor'")


class LinkSharingUpdateRequest(BaseModel):
    """
    Schema yêu cầu cập nhật cấu hình chia sẻ qua link.
    """
    share_link_access: str = Field(..., description="Chế độ chia sẻ: 'restricted' hoặc 'anyone'")
    share_link_level: str = Field(..., description="Quyền hạn qua link: 'viewer' hoặc 'editor'")

    @field_validator("share_link_access")
    @classmethod
    def validate_access(cls, v: str) -> str:
        val = v.strip().lower()
        if val not in ["restricted", "anyone"]:
            raise ValueError("Chế độ chia sẻ qua link phải là 'restricted' hoặc 'anyone'")
        return val

    @field_validator("share_link_level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        val = v.strip().lower()
        if val not in ["viewer", "editor"]:
            raise ValueError("Quyền hạn qua link phải là 'viewer' hoặc 'editor'")
        return val

