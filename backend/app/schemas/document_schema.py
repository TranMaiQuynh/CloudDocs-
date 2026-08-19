"""
schemas/document_schema.py
==========================
Mô tả:
    Pydantic schemas kiểm soát dữ liệu đầu vào/ra API cho Document.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class DocumentRenameRequest(BaseModel):
    """
    Schema cho PATCH /documents/{doc_id}/rename.
    Nhận tên mới hiển thị của tệp tin.
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Tên mới hiển thị của file (bao gồm cả phần mở rộng)",
        examples=["Báo cáo tốt nghiệp final.pdf"]
    )

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Tên tài liệu không được để trống")
        return v.strip()


class DocumentUpdateRequest(BaseModel):
    """
    Schema cho PATCH /documents/{doc_id}.
    Nhận các trường thông tin cần cập nhật của tài liệu.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Tên hiển thị mới")
    description: Optional[str] = Field(None, description="Mô tả mới")
    tags: Optional[List[str]] = Field(None, description="Danh sách nhãn mới")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Tên tài liệu không được để trống")
        return v.strip() if v is not None else None


class DocumentMoveRequest(BaseModel):
    """
    Schema cho PATCH /documents/{doc_id}/move.
    """
    target_folder_id: Optional[str] = Field(
        default=None,
        description="ID thư mục đích cần di chuyển đến, để null nếu di chuyển ra ngoài thư mục gốc."
    )


class DocumentResponse(BaseModel):
    """
    Schema trả về thông tin chi tiết (metadata) của Document.
    """
    id: str = Field(description="ID của tài liệu (MongoDB ObjectId dạng string)")
    name: str = Field(description="Tên hiển thị của tài liệu")
    folder_id: Optional[str] = Field(default=None, description="ID thư mục chứa tài liệu (null nếu ở gốc)")
    storage_path: str = Field(description="Đường dẫn lưu trữ trên Supabase Storage")
    file_size: int = Field(description="Kích thước tệp tin (byte)")
    mime_type: str = Field(description="MIME-type của tệp tin")
    current_version: int = Field(default=1, description="Phiên bản hiện tại của tài liệu")
    description: Optional[str] = Field(default="", description="Mô tả tóm tắt tài liệu")
    is_deleted: bool = Field(default=False, description="Trạng thái xóa mềm")
    tags: List[str] = Field(default=[], description="Danh sách các nhãn phân loại")
    created_by: str = Field(description="ID người tải tài liệu lên")
    created_at: datetime = Field(description="Thời gian tải lên")
    updated_at: datetime = Field(description="Thời gian cập nhật gần nhất")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "64f3c4d5e6f7a8b9c0d1e2f3",
                "name": "Báo cáo tiến độ.docx",
                "folder_id": "64f2b3c4d5e6f7a8b9c0d1e2",
                "storage_path": "folders/64f2b3c4d5e6f7a8b9c0d1e2/550e8400-e29b-41d4-a716-446655440000-Báo cáo tiến độ.docx",
                "file_size": 25480,
                "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "current_version": 1,
                "description": "Bản báo cáo tiến độ nhóm",
                "is_deleted": False,
                "created_by": "64f1a2b3c4d5e6f7a8b9c0d1",
                "created_at": "2026-08-15T12:00:00Z",
                "updated_at": "2026-08-15T12:00:00Z"
            }
        }
    }
