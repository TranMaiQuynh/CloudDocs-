"""
repositories/notification_repository.py
=======================================
Mô tả:
    Data Access Layer cho Thông báo (Notifications) trong MongoDB.
"""

from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from app.database.connection import database
from app.models.notification import create_notification_document

notifications_collection = database["notifications"]


async def create_notification(user_id: str, message: str) -> dict:
    """
    Tạo một thông báo mới cho người dùng.
    """
    notif_doc = create_notification_document(user_id=user_id, message=message)
    result = await notifications_collection.insert_one(notif_doc)
    created = await notifications_collection.find_one({"_id": result.inserted_id})
    return created


async def find_by_user(user_id: str, limit: int = 50) -> List[dict]:
    """
    Lấy danh sách thông báo của người dùng, sắp xếp mới nhất xếp trước.
    """
    try:
        user_oid = ObjectId(user_id)
    except InvalidId:
        return []
        
    cursor = notifications_collection.find({"user_id": user_oid}).sort("created_at", -1).limit(limit)
    notifs = []
    async for doc in cursor:
        notifs.append(doc)
    return notifs


async def mark_as_read(notification_id: str) -> bool:
    """
    Đánh dấu thông báo cụ thể là đã đọc.
    """
    try:
        n_oid = ObjectId(notification_id)
    except InvalidId:
        return False
        
    result = await notifications_collection.update_one(
        {"_id": n_oid},
        {"$set": {"is_read": True}}
    )
    return result.modified_count > 0


async def mark_all_as_read(user_id: str) -> bool:
    """
    Đánh dấu toàn bộ thông báo của người dùng là đã đọc.
    """
    try:
        user_oid = ObjectId(user_id)
    except InvalidId:
        return False
        
    result = await notifications_collection.update_many(
        {"user_id": user_oid, "is_read": False},
        {"$set": {"is_read": True}}
    )
    return result.modified_count > 0


def format_notification_id(notification: dict) -> dict:
    """
    Helper: Chuyển đổi ObjectId sang string.
    """
    notif_copy = dict(notification)
    if "_id" in notif_copy:
        notif_copy["id"] = str(notif_copy.pop("_id"))
    if "user_id" in notif_copy and notif_copy["user_id"] is not None:
        notif_copy["user_id"] = str(notif_copy["user_id"])
    return notif_copy
