"""
repositories/permission_repository.py
====================================
Mô tả:
    Data Access Layer cho Permission — quản trị phân quyền cộng tác viên trên MongoDB.
"""

from typing import Optional, List
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from app.database.connection import database
from app.models.permission import create_permission_document, AccessLevel

# Lấy collection "permissions" từ database
permissions_collection = database["permissions"]


async def create_indexes() -> None:
    """
    Tạo indexes cho permissions collection để tối ưu hóa tốc độ truy vấn.
    """
    # Index kiểm tra quyền truy cập của User đối với Tài nguyên
    await permissions_collection.create_index([("resource_id", 1), ("user_id", 1)])
    # Index phục vụ danh sách "Shared with me" của User
    await permissions_collection.create_index([("user_id", 1)])


async def create_permission(
    resource_id: str,
    resource_type: str,
    user_id: str,
    access_level: AccessLevel = AccessLevel.VIEWER,
    granted_by: str = "",
    share_type: str = "user",
) -> dict:
    """
    Tạo bản ghi phân quyền mới trong MongoDB.
    """
    permission_doc = create_permission_document(
        resource_id=resource_id,
        resource_type=resource_type,
        user_id=user_id,
        access_level=access_level,
        granted_by=granted_by,
        share_type=share_type,
    )

    result = await permissions_collection.insert_one(permission_doc)
    created_permission = await permissions_collection.find_one({"_id": result.inserted_id})
    return created_permission


async def find_by_id(permission_id: str) -> Optional[dict]:
    """
    Tìm bản ghi permission theo ID.
    """
    try:
        oid = ObjectId(permission_id)
    except InvalidId:
        return None

    return await permissions_collection.find_one({"_id": oid})


async def find_by_resource_and_user(
    resource_id: str,
    resource_type: str,
    user_id: str
) -> Optional[dict]:
    """
    Tìm quyền truy cập cụ thể của một User trên một Tài nguyên.
    """
    try:
        resource_oid = ObjectId(resource_id)
        user_oid = ObjectId(user_id)
    except InvalidId:
        return None

    query = {
        "resource_id": resource_oid,
        "resource_type": resource_type.strip().lower(),
        "user_id": user_oid
    }
    return await permissions_collection.find_one(query)


async def find_by_resource(resource_id: str, resource_type: str) -> List[dict]:
    """
    Lấy danh sách tất cả phân quyền/cộng tác viên của một Tài nguyên cụ thể.
    """
    try:
        resource_oid = ObjectId(resource_id)
    except InvalidId:
        return []

    query = {
        "resource_id": resource_oid,
        "resource_type": resource_type.strip().lower()
    }
    cursor = permissions_collection.find(query)
    
    permissions = []
    async for doc in cursor:
        permissions.append(doc)
    return permissions


async def find_shared_with_user(user_id: str) -> List[dict]:
    """
    Lấy toàn bộ danh sách các tài nguyên được chia sẻ cho một User cụ thể.
    """
    try:
        user_oid = ObjectId(user_id)
    except InvalidId:
        return []

    cursor = permissions_collection.find({"user_id": user_oid}).sort("created_at", -1)
    
    shared_permissions = []
    async for doc in cursor:
        shared_permissions.append(doc)
    return shared_permissions


async def update_permission(permission_id: str, access_level: AccessLevel) -> Optional[dict]:
    """
    Cập nhật cấp độ quyền truy cập của cộng tác viên.
    """
    try:
        oid = ObjectId(permission_id)
    except InvalidId:
        return None

    update_data = {
        "access_level": access_level.value,
        "updated_at": datetime.now(timezone.utc)
    }

    await permissions_collection.update_one(
        {"_id": oid},
        {"$set": update_data}
    )
    return await permissions_collection.find_one({"_id": oid})


async def delete_permission(permission_id: str) -> bool:
    """
    Xóa quyền truy cập (Thu hồi chia sẻ).
    """
    try:
        oid = ObjectId(permission_id)
    except InvalidId:
        return False

    result = await permissions_collection.delete_one({"_id": oid})
    return result.deleted_count > 0


async def delete_all_by_resource(resource_id: str, resource_type: str) -> int:
    """
    Xóa toàn bộ phân quyền liên quan đến một Tài nguyên khi tài nguyên đó bị xóa cứng.
    """
    try:
        resource_oid = ObjectId(resource_id)
    except InvalidId:
        return 0

    query = {
        "resource_id": resource_oid,
        "resource_type": resource_type.strip().lower()
    }
    result = await permissions_collection.delete_many(query)
    return result.deleted_count


def format_permission_id(permission: dict) -> dict:
    """
    Helper: Chuyển đổi ObjectId sang string phục vụ trả JSON API.
    """
    perm_copy = dict(permission)

    if "_id" in perm_copy:
        perm_copy["id"] = str(perm_copy.pop("_id"))

    if "resource_id" in perm_copy and perm_copy["resource_id"] is not None:
        perm_copy["resource_id"] = str(perm_copy["resource_id"])

    if "user_id" in perm_copy and perm_copy["user_id"] is not None:
        perm_copy["user_id"] = str(perm_copy["user_id"])

    if "granted_by" in perm_copy and perm_copy["granted_by"] is not None:
        perm_copy["granted_by"] = str(perm_copy["granted_by"])

    if "share_type" not in perm_copy or perm_copy["share_type"] is None:
        perm_copy["share_type"] = "user"

    return perm_copy
