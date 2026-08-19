"""
models/document.py
==================
Mô tả:
    Đây là Data Model đại diện cho một Document metadata trong MongoDB.
    Model này định nghĩa cấu trúc dữ liệu, hỗ trợ cơ chế xóa mềm (Soft Delete).
"""

from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId


def create_document_document(
    name: str,
    folder_id: Optional[str],
    storage_path: str,
    file_size: int,
    mime_type: str,
    created_by: str,
    current_version: int = 1,
    description: str = "",
    is_deleted: bool = False,
    deleted_at: Optional[datetime] = None,
    tags: list = [],
) -> dict:
    """
    Factory function tạo một document metadata mới để lưu vào MongoDB.

    Args:
        name:            Tên hiển thị của tệp tin (ví dụ: "Báo cáo.pdf")
        folder_id:       ID của thư mục chứa tài liệu này (string hoặc None nếu ở root)
        storage_path:    Đường dẫn lưu trữ vật lý trên Supabase Storage
        file_size:       Kích thước file (bytes)
        mime_type:       Định dạng MIME-type của file
        created_by:      ID người tải tệp tin lên (string)
        current_version: Phiên bản hiện tại của tài liệu (mặc định: 1)
        description:     Mô tả ngắn gọn về tài liệu (mặc định: "")
        is_deleted:      Trạng thái xóa mềm (mặc định: False - chưa xóa)
        deleted_at:      Thời điểm xóa mềm (mặc định: None - chưa xóa)
        tags:            Danh sách nhãn dán phân loại tệp tin

    Returns:
        dict: Document metadata sẵn sàng lưu vào MongoDB collection "documents"
    """
    now = datetime.now(timezone.utc)

    # Chuyển đổi ID dạng chuỗi -> ObjectId của MongoDB
    folder_oid = ObjectId(folder_id) if folder_id else None
    created_by_oid = ObjectId(created_by) if created_by else None

    return {
        "name": name.strip(),
        "folder_id": folder_oid,
        "storage_path": storage_path,
        "file_size": file_size,
        "mime_type": mime_type,
        "created_by": created_by_oid,
        "current_version": current_version,
        "description": description.strip(),
        "is_deleted": is_deleted,
        "deleted_at": deleted_at,
        "tags": tags,
        "created_at": now,
        "updated_at": now,
    }
