"""
schemas/comment_schema.py
=========================
Mô tả:
    Pydantic schemas quản lý dữ liệu đầu vào/đầu ra cho Bình luận (Comments).
"""

from pydantic import BaseModel, Field
from datetime import datetime


class CommentCreateRequest(BaseModel):
    """
    Schema cho POST /documents/{doc_id}/comments.
    """
    content: str = Field(..., min_length=1, description="Nội dung bình luận/ghi chú")


class CommentResponse(BaseModel):
    """
    Schema phản hồi thông tin bình luận.
    """
    id: str = Field(description="ID bình luận")
    document_id: str = Field(description="ID tài liệu")
    user_id: str = Field(description="ID người bình luận")
    user_name: str = Field(description="Tên hiển thị người bình luận")
    content: str = Field(description="Nội dung bình luận")
    created_at: datetime = Field(description="Thời gian tạo")

    model_config = {
        "from_attributes": True
    }
