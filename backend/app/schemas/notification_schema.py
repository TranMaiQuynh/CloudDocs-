"""
schemas/notification_schema.py
==============================
Mô tả:
    Pydantic schemas quản lý thông báo (Notifications).
"""

from pydantic import BaseModel, Field
from datetime import datetime


class NotificationResponse(BaseModel):
    """
    Schema trả về thông tin thông báo.
    """
    id: str = Field(description="ID thông báo (MongoDB ObjectId dạng string)")
    user_id: str = Field(description="ID người nhận thông báo")
    message: str = Field(description="Nội dung thông báo")
    is_read: bool = Field(description="Trạng thái đã đọc")
    created_at: datetime = Field(description="Thời gian tạo")

    model_config = {
        "from_attributes": True
    }
