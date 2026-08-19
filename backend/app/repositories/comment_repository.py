"""
repositories/comment_repository.py
==================================
Mô tả:
    Data Access Layer cho Comments — lưu trữ các bình luận/ghi chú của tài liệu.
"""

from typing import List
from datetime import datetime, timezone
from bson import ObjectId
from app.database.connection import database

comments_collection = database["comments"]


async def create_comment(
    document_id: str,
    user_id: str,
    user_name: str,
    content: str
) -> dict:
    """
    Tạo bình luận mới trên tài liệu.
    """
    now = datetime.now(timezone.utc)
    comment_doc = {
        "document_id": ObjectId(document_id),
        "user_id": ObjectId(user_id),
        "user_name": user_name,
        "content": content.strip(),
        "created_at": now
    }
    result = await comments_collection.insert_one(comment_doc)
    created = await comments_collection.find_one({"_id": result.inserted_id})
    return created


async def find_by_document(document_id: str) -> List[dict]:
    """
    Lấy toàn bộ bình luận của một tài liệu, sắp xếp từ cũ nhất đến mới nhất.
    """
    cursor = comments_collection.find({"document_id": ObjectId(document_id)}).sort("created_at", 1)
    comments = []
    async for doc in cursor:
        comments.append(doc)
    return comments


def format_comment_id(comment: dict) -> dict:
    """
    Helper format ObjectId sang String.
    """
    c_copy = dict(comment)
    if "_id" in c_copy:
        c_copy["id"] = str(c_copy.pop("_id"))
    if "document_id" in c_copy:
        c_copy["document_id"] = str(c_copy["document_id"])
    if "user_id" in c_copy:
        c_copy["user_id"] = str(c_copy["user_id"])
    return c_copy
