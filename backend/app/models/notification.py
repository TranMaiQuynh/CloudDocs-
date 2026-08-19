"""
models/notification.py
======================
Mô tả:
    Data Model đại diện cho một thông báo (Notification) trong MongoDB.
"""

from datetime import datetime, timezone
from bson import ObjectId


def create_notification_document(
    user_id: str,
    message: str,
    is_read: bool = False,
) -> dict:
    """
    Factory function tạo một notification document mới.
    """
    now = datetime.now(timezone.utc)
    user_oid = ObjectId(user_id) if user_id else None

    return {
        "user_id": user_oid,
        "message": message.strip(),
        "is_read": is_read,
        "created_at": now,
    }
