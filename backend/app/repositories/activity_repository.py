"""
repositories/activity_repository.py
==================================
Mô tả:
    Data Access Layer cho Activity Logs (Audit Trail) — ghi nhận lịch sử thao tác hệ thống.
"""

from typing import List
from datetime import datetime, timezone
from bson import ObjectId
from app.database.connection import database

activities_collection = database["activities"]


async def create_activity(
    user_id: str,
    user_name: str,
    action: str,
    resource_name: str,
    details: str = ""
) -> dict:
    """
    Ghi nhận một hoạt động hệ thống.
    """
    now = datetime.now(timezone.utc)
    activity_doc = {
        "user_id": ObjectId(user_id) if user_id else None,
        "user_name": user_name,
        "action": action.upper(),  # UPLOAD, DELETE, SHARE, etc.
        "resource_name": resource_name,
        "details": details,
        "created_at": now
    }
    result = await activities_collection.insert_one(activity_doc)
    created = await activities_collection.find_one({"_id": result.inserted_id})
    return created


async def find_all_activities(limit: int = 100) -> List[dict]:
    """
    Lấy danh sách nhật ký hoạt động hệ thống, sắp xếp mới nhất lên đầu.
    """
    cursor = activities_collection.find({}).sort("created_at", -1).limit(limit)
    activities = []
    async for doc in cursor:
        activities.append(doc)
    return activities


async def find_by_user(user_id: str, limit: int = 50) -> List[dict]:
    """
    Lấy danh sách nhật ký hoạt động của riêng một User.
    """
    cursor = activities_collection.find({"user_id": ObjectId(user_id)}).sort("created_at", -1).limit(limit)
    activities = []
    async for doc in cursor:
        activities.append(doc)
    return activities


def format_activity_id(activity: dict) -> dict:
    """
    Helper format ObjectId sang String.
    """
    a_copy = dict(activity)
    if "_id" in a_copy:
        a_copy["id"] = str(a_copy.pop("_id"))
    if "user_id" in a_copy and a_copy["user_id"] is not None:
        a_copy["user_id"] = str(a_copy["user_id"])
    return a_copy
