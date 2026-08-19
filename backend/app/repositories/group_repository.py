"""
repositories/group_repository.py
================================
Mô tả:
    Data Access Layer cho Nhóm học tập (Study Groups) trong MongoDB.
"""

from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
import uuid
from app.database.connection import database
from app.models.group import create_group_document

groups_collection = database["groups"]


async def populate_member_details(group: Optional[dict]) -> Optional[dict]:
    """
    Tìm thông tin email và full_name của các thành viên trong nhóm và gắn vào dict.
    """
    if not group:
        return group
    
    member_details = []
    member_ids = group.get("members", [])
    if member_ids:
        # Lấy danh sách ObjectIds
        oids = []
        for m in member_ids:
            if isinstance(m, ObjectId):
                oids.append(m)
            else:
                try:
                    oids.append(ObjectId(str(m)))
                except Exception:
                    pass
        
        # Query users collection
        users_cursor = database["users"].find({"_id": {"$in": oids}})
        user_map = {}
        async for u in users_cursor:
            user_map[str(u["_id"])] = {
                "id": str(u["_id"]),
                "email": u.get("email", ""),
                "full_name": u.get("full_name", "")
            }
        
        # Duy trì thứ tự của member_ids
        for m in member_ids:
            m_str = str(m)
            if m_str in user_map:
                member_details.append(user_map[m_str])
            else:
                member_details.append({
                    "id": m_str,
                    "email": m_str,
                    "full_name": "Người dùng hệ thống"
                })
    
    group["member_details"] = member_details
    return group


async def create_group(
    name: str,
    created_by: str,
    description: str = "",
    members: List[str] = []
) -> dict:
    """
    Tạo nhóm học tập mới và lưu vào MongoDB.
    """
    group_doc = create_group_document(
        name=name,
        created_by=created_by,
        description=description,
        members=members
    )
    result = await groups_collection.insert_one(group_doc)
    created = await groups_collection.find_one({"_id": result.inserted_id})
    return await populate_member_details(created)


async def ensure_invite_code(group: Optional[dict]) -> Optional[dict]:
    """
    Đảm bảo nhóm luôn có mã mời (invite_code). Nếu không có, tự động tạo mới và lưu vào DB.
    """
    if not group:
        return group
    if not group.get("invite_code"):
        code = uuid.uuid4().hex[:12]
        await groups_collection.update_one(
            {"_id": group["_id"]},
            {"$set": {"invite_code": code}}
        )
        group["invite_code"] = code
    return group


async def find_by_id(group_id: str) -> Optional[dict]:
    """
    Tìm nhóm học tập theo ID.
    """
    try:
        oid = ObjectId(group_id)
    except InvalidId:
        return None
    group = await groups_collection.find_one({"_id": oid})
    healed = await ensure_invite_code(group)
    return await populate_member_details(healed)


async def find_user_groups(user_id: str) -> List[dict]:
    """
    Tìm tất cả các nhóm học tập mà người dùng tham gia (là chủ hoặc là thành viên).
    """
    try:
        user_oid = ObjectId(user_id)
    except InvalidId:
        return []
    
    # Tìm các nhóm mà members chứa user_oid
    cursor = groups_collection.find({"members": user_oid}).sort("created_at", -1)
    
    groups = []
    async for doc in cursor:
        healed_doc = await ensure_invite_code(doc)
        populated = await populate_member_details(healed_doc)
        groups.append(populated)
    return groups


async def add_member(group_id: str, user_id: str) -> bool:
    """
    Thêm một thành viên vào nhóm học tập.
    """
    try:
        g_oid = ObjectId(group_id)
        u_oid = ObjectId(user_id)
    except InvalidId:
        return False
        
    result = await groups_collection.update_one(
        {"_id": g_oid},
        {"$addToSet": {"members": u_oid}, "$set": {"updated_at": datetime.now(timezone.utc)}}
    )
    return result.modified_count > 0


async def remove_member(group_id: str, user_id: str) -> bool:
    """
    Xóa một thành viên khỏi nhóm học tập.
    """
    try:
        g_oid = ObjectId(group_id)
        u_oid = ObjectId(user_id)
    except InvalidId:
        return False
        
    result = await groups_collection.update_one(
        {"_id": g_oid},
        {"$pull": {"members": u_oid}, "$set": {"updated_at": datetime.now(timezone.utc)}}
    )
    return result.modified_count > 0


async def find_by_invite_code(invite_code: str) -> Optional[dict]:
    """
    Tìm nhóm học tập theo mã mời (invite code) dùng cho link mời.
    """
    if not invite_code:
        return None
    group = await groups_collection.find_one({"invite_code": invite_code})
    healed = await ensure_invite_code(group)
    return await populate_member_details(healed)


async def add_pending_member(group_id: str, user_id: str, email: str, full_name: str) -> bool:
    """
    Thêm một thành viên đang chờ phê duyệt vào nhóm học tập.
    """
    try:
        g_oid = ObjectId(group_id)
        u_oid = ObjectId(user_id)
    except InvalidId:
        return False
    
    # Kiểm tra xem đã tồn tại yêu cầu từ user_id này chưa
    existing = await groups_collection.find_one({"_id": g_oid, "pending_members.user_id": u_oid})
    if existing:
        return True
        
    result = await groups_collection.update_one(
        {"_id": g_oid},
        {
            "$push": {
                "pending_members": {
                    "user_id": u_oid,
                    "email": email,
                    "full_name": full_name
                }
            },
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )
    return result.modified_count > 0


async def remove_pending_member(group_id: str, user_id: str) -> bool:
    """
    Xóa một người dùng khỏi danh sách chờ phê duyệt của nhóm học tập.
    """
    try:
        g_oid = ObjectId(group_id)
        u_oid = ObjectId(user_id)
    except InvalidId:
        return False
        
    result = await groups_collection.update_one(
        {"_id": g_oid},
        {
            "$pull": {
                "pending_members": {"user_id": u_oid}
            },
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )
    return result.modified_count > 0


def format_group_id(group: dict) -> dict:
    """
    Helper: Chuyển đổi ObjectId sang string.
    """
    group_copy = dict(group)
    if "_id" in group_copy:
        group_copy["id"] = str(group_copy.pop("_id"))
    if "created_by" in group_copy and group_copy["created_by"] is not None:
        group_copy["created_by"] = str(group_copy["created_by"])
    if "member_details" in group_copy and group_copy["member_details"] is not None:
        group_copy["members"] = group_copy["member_details"]
    elif "members" in group_copy and group_copy["members"] is not None:
        group_copy["members"] = [{"id": str(m), "email": str(m), "full_name": ""} for m in group_copy["members"]]
    # Đảm bảo invite_code luôn tồn tại
    if "invite_code" not in group_copy:
        group_copy["invite_code"] = ""
    # Format pending_members
    if "pending_members" in group_copy and group_copy["pending_members"] is not None:
        formatted_pm = []
        for pm in group_copy["pending_members"]:
            formatted_pm.append({
                "user_id": str(pm["user_id"]),
                "email": pm.get("email", ""),
                "full_name": pm.get("full_name", "")
            })
        group_copy["pending_members"] = formatted_pm
    else:
        group_copy["pending_members"] = []
    return group_copy


async def update_group(
    group_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Optional[dict]:
    """
    Cập nhật thông tin (tên, mô tả) của nhóm học tập.
    """
    try:
        g_oid = ObjectId(group_id)
    except InvalidId:
        return None

    update_fields = {"updated_at": datetime.now(timezone.utc)}
    if name is not None:
        update_fields["name"] = name
    if description is not None:
        update_fields["description"] = description

    await groups_collection.update_one(
        {"_id": g_oid},
        {"$set": update_fields}
    )
    return await find_by_id(group_id)


async def delete_group(group_id: str) -> bool:
    """
    Xóa hẳn một nhóm học tập và dọn dẹp các quyền liên quan.
    """
    try:
        g_oid = ObjectId(group_id)
    except InvalidId:
        return False

    result = await groups_collection.delete_one({"_id": g_oid})
    if result.deleted_count > 0:
        # Dọn dẹp permissions liên quan đến nhóm này
        await database["permissions"].delete_many({
            "share_type": "group",
            "user_id": g_oid
        })
        return True
    return False

