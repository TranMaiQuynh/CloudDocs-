"""
schemas/activity_schema.py
==========================
Mô tả:
    Pydantic schemas quản lý phản hồi dữ liệu cho Nhật ký hoạt động (Activities).
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ActivityResponse(BaseModel):
    """
    Schema phản hồi nhật ký hoạt động hệ thống.
    """
    id: str = Field(description="ID bản ghi nhật ký")
    user_id: Optional[str] = Field(None, description="ID người thực hiện")
    user_name: str = Field(description="Tên người thực hiện")
    action: str = Field(description="Thao tác: UPLOAD, DELETE, SHARE...")
    resource_name: str = Field(description="Tên tài nguyên chịu tác động")
    details: str = Field(description="Chi tiết bổ sung")
    created_at: datetime = Field(description="Thời gian thực hiện")

    model_config = {
        "from_attributes": True
    }
