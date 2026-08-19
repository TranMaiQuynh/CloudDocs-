"""
services/permission_service.py
==========================
Mô tả:
    Business Logic Layer cho Phân quyền (Permissions) và Kế thừa Quyền (Permission Inheritance).
    Xử lý kiểm tra quyền đệ quy ngược cây thư mục cha.
"""

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.repositories import permission_repository, user_repository, document_repository, folder_repository, notification_repository, group_repository
from app.schemas.permission_schema import PermissionCreateRequest, PermissionUpdateRequest, LinkSharingUpdateRequest
from app.models.permission import AccessLevel
from bson import ObjectId
from app.database.connection import database

users_collection = database["users"]


async def share_resource(request: PermissionCreateRequest, granted_by: str) -> dict:
    """
    Chia sẻ tài nguyên (tài liệu/thư mục) cho một tài khoản khác qua Email hoặc nhóm học tập.
    """
    # 1. Tìm thông tin tài nguyên và tên hiển thị để ghi vào thông báo
    resource_name = "Tài nguyên"
    if request.resource_type == "document":
        doc = await document_repository.find_by_id(request.resource_id, include_deleted=True)
        if doc:
            resource_name = doc["name"]
    else:
        folder = await folder_repository.find_by_id(request.resource_id, include_deleted=True)
        if folder:
            resource_name = folder["name"]

    # 2. Kiểm tra quyền của người chia sẻ (phải có Editor trở lên hoặc Owner)
    has_rights = await check_user_access(
        user_id=granted_by,
        resource_id=request.resource_id,
        resource_type=request.resource_type,
        required_level=AccessLevel.EDITOR
    )
    if not has_rights:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền chia sẻ tài nguyên này. Yêu cầu quyền Editor trở lên."
        )

    # 3. Phân nhánh xử lý chia sẻ theo User hoặc Group
    recipient_id = ""
    recipient_email = None
    group_name = None
    group = None

    if request.share_type == "group":
        if not request.group_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thiếu group_id khi chia sẻ cho nhóm học tập."
            )
        group = await group_repository.find_by_id(request.group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nhóm học tập nhận quyền chia sẻ không tồn tại."
            )
        recipient_id = request.group_id
        group_name = group["name"]
    else:
        if not request.user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thiếu email người nhận quyền chia sẻ."
            )
        recipient = await user_repository.find_by_email(request.user_email)
        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Người dùng được chia sẻ không tồn tại trong hệ thống."
            )
        recipient_id = str(recipient["_id"])
        recipient_email = recipient["email"]
        if recipient_id == granted_by:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bạn không thể tự chia sẻ tài nguyên cho chính mình."
            )

    # 4. Kiểm tra xem đã có phân quyền trùng lặp chưa
    existing = await database["permissions"].find_one({
        "resource_id": ObjectId(request.resource_id),
        "resource_type": request.resource_type,
        "user_id": ObjectId(recipient_id),
        "share_type": request.share_type
    })

    if existing:
        updated = await permission_repository.update_permission(
            permission_id=str(existing["_id"]),
            access_level=request.access_level
        )
        res = permission_repository.format_permission_id(updated)
        res["user_email"] = recipient_email
        res["group_name"] = group_name
        return res

    # 5. Lưu quyền vào MongoDB
    new_perm = await permission_repository.create_permission(
        resource_id=request.resource_id,
        resource_type=request.resource_type,
        user_id=recipient_id,
        access_level=request.access_level,
        granted_by=granted_by,
        share_type=request.share_type
    )

    # 6. Gửi thông báo 🔔
    if request.share_type == "user":
        await notification_repository.create_notification(
            user_id=recipient_id,
            message=f"Bạn đã được chia sẻ quyền {request.access_level.value} trên tài liệu/thư mục '{resource_name}'."
        )
    elif request.share_type == "group" and group:
        # Gửi thông báo đến mọi thành viên của nhóm học tập (trừ người chia sẻ)
        for member_oid in group.get("members", []):
            member_id = str(member_oid)
            if member_id != granted_by:
                await notification_repository.create_notification(
                    user_id=member_id,
                    message=f"Nhóm '{group_name}' đã được chia sẻ quyền {request.access_level.value} trên '{resource_name}'."
                )

    res = permission_repository.format_permission_id(new_perm)
    res["user_email"] = recipient_email
    res["group_name"] = group_name
    return res


async def get_resource_collaborators(resource_id: str, resource_type: str, user_id: str) -> List[dict]:
    """
    Lấy danh sách tất cả những người đang được chia sẻ quyền trên tài nguyên này.
    Yêu cầu người gọi có quyền đọc trên tài nguyên.
    """
    # Xác minh quyền đọc
    has_read = await check_user_access(user_id, resource_id, resource_type, AccessLevel.VIEWER)
    if not has_read:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xem thông tin chia sẻ của tài nguyên này."
        )

    perms = await permission_repository.find_by_resource(resource_id, resource_type)
    
    # Kết hợp email hoặc tên nhóm để hiển thị đẹp mắt ở Frontend
    results = []
    for p in perms:
        formatted = permission_repository.format_permission_id(p)
        if p.get("share_type") == "group":
            group = await database["groups"].find_one({"_id": p["user_id"]}, {"name": 1})
            formatted["group_name"] = group["name"] if group else "Nhóm học tập"
            formatted["user_email"] = None
        else:
            recipient = await users_collection.find_one({"_id": p["user_id"]}, {"email": 1})
            formatted["user_email"] = recipient["email"] if recipient else "unknown@university.edu.vn"
            formatted["group_name"] = None
        results.append(formatted)
        
    return results


async def revoke_permission(permission_id: str, user_id: str) -> dict:
    """
    Thu hồi quyền chia sẻ (Xóa phân quyền).
    Chỉ Admin, Owner hoặc chính cộng tác viên tự hủy chia sẻ mới được thực hiện.
    """
    perm = await permission_repository.find_by_id(permission_id)
    if not perm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bản ghi phân quyền không tồn tại."
        )

    # Kiểm tra quyền: Admin, Owner tài nguyên hoặc chính người được phân quyền tự gỡ
    is_recipient = str(perm["user_id"]) == user_id
    has_admin_rights = await check_user_access(user_id, str(perm["resource_id"]), perm["resource_type"], AccessLevel.EDITOR)

    if not is_recipient and not has_admin_rights:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền thu hồi chia sẻ trên tài nguyên này."
        )

    success = await permission_repository.delete_permission(permission_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể thu hồi quyền chia sẻ."
        )

    return {
        "success": True,
        "message": "Đã thu hồi quyền chia sẻ thành công."
    }


async def check_user_access(
    user_id: str,
    resource_id: str,
    resource_type: str,
    required_level: AccessLevel = AccessLevel.VIEWER,
    allow_link_sharing: bool = True
) -> bool:
    """
    HÀM CỐT LÕI: Xác định xem một User có quyền truy cập vào Tài nguyên hay không.
    Tích hợp cơ chế Kế thừa Quyền đệ quy (Cascading Permission Inheritance) lên cấp thư mục cha.
    """
    # 1. Quét vai trò hệ thống: Quyền Admin toàn quyền
    try:
        user_oid = ObjectId(user_id)
    except:
        return False
    user = await users_collection.find_one({"_id": user_oid}, {"role": 1})
    if user and user.get("role") == "admin":
        return True

    # 2. Kiểm tra quyền sở hữu gốc (Owner Check) & Chia sẻ link
    if resource_type == "document":
        doc = await document_repository.find_by_id(resource_id, include_deleted=True)
        if not doc:
            return False
        if str(doc.get("created_by")) == user_id:
            return True
        # Kiểm tra chia sẻ qua link (anyone with link)
        if allow_link_sharing and doc.get("share_link_access") == "anyone":
            user_level = doc.get("share_link_level", "viewer")
            if required_level == AccessLevel.VIEWER or user_level == AccessLevel.EDITOR:
                return True
        parent_id = str(doc["folder_id"]) if doc.get("folder_id") else None
    
    elif resource_type == "folder":
        folder = await folder_repository.find_by_id(resource_id, include_deleted=True)
        if not folder:
            return False
        if str(folder.get("created_by")) == user_id:
            return True
        # Kiểm tra chia sẻ qua link (anyone with link)
        if allow_link_sharing and folder.get("share_link_access") == "anyone":
            user_level = folder.get("share_link_level", "viewer")
            if required_level == AccessLevel.VIEWER or user_level == AccessLevel.EDITOR:
                return True
        parent_id = str(folder["parent_id"]) if folder.get("parent_id") else None
    
    else:
        return False

    # 3. Kiểm tra phân quyền trực tiếp trên tài nguyên này
    direct_perm = await permission_repository.find_by_resource_and_user(
        resource_id=resource_id,
        resource_type=resource_type,
        user_id=user_id
    )

    if direct_perm:
        user_level = direct_perm.get("access_level")
        if required_level == AccessLevel.VIEWER:
            return user_level in [AccessLevel.VIEWER, AccessLevel.EDITOR]
        elif required_level == AccessLevel.EDITOR:
            return user_level == AccessLevel.EDITOR

    # 3.5. Kiểm tra phân quyền thông qua nhóm học tập (Group-Based ACL)
    cursor_g = database["groups"].find({"members": user_oid}, {"_id": 1})
    group_oids = []
    async for g in cursor_g:
        group_oids.append(g["_id"])

    if group_oids:
        group_perm = await database["permissions"].find_one({
            "resource_id": ObjectId(resource_id),
            "resource_type": resource_type,
            "share_type": "group",
            "user_id": {"$in": group_oids}
        })
        if group_perm:
            user_level = group_perm.get("access_level")
            if required_level == AccessLevel.VIEWER:
                if user_level in [AccessLevel.VIEWER, AccessLevel.EDITOR]:
                    return True
            elif required_level == AccessLevel.EDITOR:
                if user_level == AccessLevel.EDITOR:
                    return True

    # 4. Cơ chế Kế thừa Quyền đệ quy (Recursive Inheritance)
    # Nếu không có quyền trực tiếp, đi ngược lên thư mục cha (nếu có)
    if parent_id:
        return await check_user_access(
            user_id=user_id,
            resource_id=parent_id,
            resource_type="folder",
            required_level=required_level
        )

    # Lên tận gốc mà không tìm thấy phân quyền
    return False


async def get_link_sharing(resource_id: str, resource_type: str, user_id: str) -> dict:
    """
    Lấy cấu hình chia sẻ qua link của tài nguyên.
    """
    has_read = await check_user_access(user_id, resource_id, resource_type, AccessLevel.VIEWER)
    if not has_read:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xem cấu hình chia sẻ của tài nguyên này."
        )

    if resource_type == "document":
        res = await document_repository.find_by_id(resource_id, include_deleted=True)
    else:
        res = await folder_repository.find_by_id(resource_id, include_deleted=True)

    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tài nguyên không tồn tại."
        )

    return {
        "share_link_access": res.get("share_link_access", "restricted"),
        "share_link_level": res.get("share_link_level", "viewer")
    }


async def update_link_sharing(
    resource_id: str,
    resource_type: str,
    share_link_access: str,
    share_link_level: str,
    user_id: str
) -> dict:
    """
    Cập nhật cấu hình chia sẻ qua link.
    Yêu cầu quyền Editor trở lên hoặc là Owner của tài nguyên.
    """
    # 1. Kiểm tra quyền ghi (Editor)
    has_write = await check_user_access(user_id, resource_id, resource_type, AccessLevel.EDITOR)
    if not has_write:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền thay đổi cấu hình chia sẻ của tài nguyên này."
        )

    # 2. Thực hiện cập nhật
    collection_name = "documents" if resource_type == "document" else "folders"
    try:
        oid = ObjectId(resource_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID tài nguyên không hợp lệ."
        )

    result = await database[collection_name].update_one(
        {"_id": oid},
        {
            "$set": {
                "share_link_access": share_link_access,
                "share_link_level": share_link_level,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy tài nguyên để cập nhật."
        )

    return {
        "share_link_access": share_link_access,
        "share_link_level": share_link_level
    }
