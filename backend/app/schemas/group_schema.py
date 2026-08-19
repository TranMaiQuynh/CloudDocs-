"""
schemas/group_schema.py
=======================
Mô tả:
    Pydantic schemas quản lý Nhóm học tập (Study Groups).
"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime


class GroupCreateRequest(BaseModel):
    """
    Schema nhận dữ liệu khi tạo nhóm học tập mới.
    """
    name: str = Field(..., min_length=1, max_length=100, description="Tên nhóm học tập")
    description: Optional[str] = Field(default="", max_length=500, description="Mô tả nhóm")
    members: List[str] = Field(default=[], description="Danh sách ID người dùng thành viên ban đầu")


class GroupUpdateRequest(BaseModel):
    """
    Schema nhận dữ liệu khi cập nhật thông tin nhóm học tập.
    """
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Tên nhóm mới")
    description: Optional[str] = Field(default=None, max_length=500, description="Mô tả mới")


class GroupMemberRequest(BaseModel):
    """
    Schema nhận dữ liệu mời thành viên mới vào nhóm bằng email.
    """
    email: EmailStr = Field(..., description="Email học tập của thành viên cần mời")


class PendingMember(BaseModel):
    """
    Schema đại diện cho yêu cầu tham gia nhóm học tập đang chờ duyệt.
    """
    user_id: str = Field(description="ID người dùng gửi yêu cầu")
    email: str = Field(description="Email người dùng")
    full_name: str = Field(default="", description="Họ tên người dùng")


class GroupMemberResponse(BaseModel):
    """
    Schema trả về thông tin chi tiết thành viên nhóm.
    """
    id: str = Field(description="ID người dùng")
    email: str = Field(description="Email người dùng")
    full_name: str = Field(default="", description="Họ tên người dùng")


class GroupResponse(BaseModel):
    """
    Schema trả về thông tin chi tiết Nhóm học tập.
    """
    id: str = Field(description="ID nhóm (MongoDB ObjectId dạng string)")
    name: str = Field(description="Tên nhóm")
    description: Optional[str] = Field(default="", description="Mô tả nhóm")
    created_by: str = Field(description="ID người tạo nhóm")
    members: List[GroupMemberResponse] = Field(description="Danh sách thành viên trong nhóm")
    invite_code: str = Field(default="", description="Mã mời dùng để tạo link chia sẻ")
    pending_members: List[PendingMember] = Field(default=[], description="Danh sách yêu cầu chờ duyệt")
    created_at: datetime = Field(description="Thời gian tạo")
    updated_at: datetime = Field(description="Thời gian cập nhật")

    model_config = {
        "from_attributes": True
    }
