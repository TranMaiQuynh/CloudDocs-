"""
models/folder.py
================
Mô tả:
    Đây là Data Model đại diện cho một Folder document trong MongoDB.
    Model này định nghĩa cấu trúc dữ liệu, hỗ trợ cơ chế xóa mềm (Soft Delete).
"""

from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId


def create_folder_document(
    name: str,
    parent_id: Optional[str] = None,
    created_by: str = "",
    description: str = "",
    is_deleted: bool = False,
    deleted_at: Optional[datetime] = None,
    tags: list = [],
) -> dict:
    """
    Factory function tạo một folder document mới để lưu vào MongoDB.

    Args:
        name:        Tên thư mục
        parent_id:   ID của thư mục cha (string hoặc None)
        created_by:  ID của người tạo thư mục (string)
        description: Mô tả ngắn gọn về thư mục (mặc định: "")
        is_deleted:  Trạng thái xóa mềm (mặc định: False - chưa xóa)
        deleted_at:  Thời điểm xóa mềm (mặc định: None - chưa xóa)
        tags:        Danh sách thẻ nhãn môn học/phân loại

    Returns:
        dict: Document sẵn sàng để insert vào MongoDB collection "folders"
    """
    now = datetime.now(timezone.utc)

    # Chuyển đổi ID string -> MongoDB ObjectId
    parent_oid = ObjectId(parent_id) if parent_id else None
    created_by_oid = ObjectId(created_by) if created_by else None

    return {
        "name": name.strip(),
        "parent_id": parent_oid,
        "created_by": created_by_oid,
        "description": description.strip(),
        "is_deleted": is_deleted,
        "deleted_at": deleted_at,
        "tags": tags,
        "created_at": now,
        "updated_at": now,
    }
