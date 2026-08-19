"""
models/version.py
=================
Mô tả:
    Đây là Data Model đại diện cho một Version document trong MongoDB.
    Hỗ trợ quản lý lịch sử phiên bản của tài liệu.
"""

from datetime import datetime, timezone
from bson import ObjectId


def create_version_document(
    document_id: str,
    version_number: int,
    storage_path: str,
    file_size: int,
    created_by: str,
    change_log: str = "",
) -> dict:
    """
    Factory function tạo một version document mới để lưu vào MongoDB.

    Args:
        document_id:    ID của tài liệu (string)
        version_number: Số phiên bản (ví dụ: 1, 2, 3...)
        storage_path:   Đường dẫn lưu trữ vật lý trên Supabase Storage
        file_size:      Kích thước file phiên bản (bytes)
        created_by:     ID người upload phiên bản này (string)
        change_log:     Mô tả các thay đổi trong phiên bản này (mặc định: "")

    Returns:
        dict: Document sẵn sàng để insert vào MongoDB collection "versions"
    """
    now = datetime.now(timezone.utc)

    document_oid = ObjectId(document_id) if document_id else None
    created_by_oid = ObjectId(created_by) if created_by else None

    return {
        "document_id": document_oid,
        "version_number": version_number,
        "storage_path": storage_path,
        "file_size": file_size,
        "created_by": created_by_oid,
        "change_log": change_log.strip(),
        "created_at": now,
    }
