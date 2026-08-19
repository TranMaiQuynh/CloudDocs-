"""
schemas/version_schema.py
=========================
Mô tả:
    Pydantic schemas quản trị dữ liệu đầu ra cho Lịch sử Phiên bản (Versions).
"""

from pydantic import BaseModel, Field
from datetime import datetime


class VersionResponse(BaseModel):
    """
    Schema phản hồi thông tin chi tiết một phiên bản tài liệu lịch sử.
    """
    id: str = Field(description="ID bản ghi phiên bản")
    document_id: str = Field(description="ID của tài liệu gốc")
    version_number: int = Field(description="Số thứ tự phiên bản (1, 2, 3...)")
    storage_path: str = Field(description="Đường dẫn lưu trên Supabase Storage")
    file_size: int = Field(description="Kích thước tệp (bytes)")
    created_by: str = Field(description="ID người tải lên phiên bản này")
    change_log: str = Field(description="Mô tả thay đổi của phiên bản")
    created_at: datetime = Field(description="Thời gian tạo")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "64f3e6f7a8b9c0d1e2f3a4b5",
                "document_id": "64f3c4d5e6f7a8b9c0d1e2f3",
                "version_number": 2,
                "storage_path": "folders/64f2b3c4d5e6f7a8b9c0d1e2/Báo cáo tốt nghiệp v2.pdf",
                "file_size": 18240,
                "created_by": "64f1a2b3c4d5e6f7a8b9c0d1",
                "change_log": "Chỉnh sửa chương 1 và chương 2.",
                "created_at": "2026-08-15T12:00:00Z"
            }
        }
    }
