"""
routers/groups.py
=================
Mô tả:
    API Router quản lý Nhóm học tập (Study Groups).
"""

from fastapi import APIRouter, Depends, status, HTTPException
from typing import List
from bson import ObjectId
from app.schemas.group_schema import GroupCreateRequest, GroupUpdateRequest, GroupMemberRequest, GroupResponse
from app.repositories import group_repository, notification_repository
from app.dependencies.auth_deps import get_current_user
from app.database.connection import database

users_collection = database["users"]

router = APIRouter(
    prefix="/groups",
    tags=["Groups"],
)


@router.post(
    "",
    response_model=GroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo nhóm học tập mới",
)
async def create_new_group(
    request: GroupCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    group = await group_repository.create_group(
        name=request.name,
        created_by=current_user["id"],
        description=request.description or "",
        members=request.members
    )
    return group_repository.format_group_id(group)


@router.get(
    "",
    response_model=List[GroupResponse],
    status_code=status.HTTP_200_OK,
    summary="Xem danh sách nhóm học tập tham gia",
)
async def list_groups(
    current_user: dict = Depends(get_current_user)
):
    groups = await group_repository.find_user_groups(current_user["id"])
    return [group_repository.format_group_id(g) for g in groups]


@router.post(
    "/join/{invite_code}",
    response_model=GroupResponse,
    status_code=status.HTTP_200_OK,
    summary="Tham gia nhóm học tập qua link mời (invite code)",
)
async def join_group_via_link(
    invite_code: str,
    current_user: dict = Depends(get_current_user)
):
    # 1. Tìm nhóm theo invite_code
    group = await group_repository.find_by_invite_code(invite_code)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mã mời không hợp lệ hoặc nhóm không tồn tại."
        )

    user_oid = ObjectId(current_user["id"])

    # 2. Kiểm tra xem đã là thành viên chưa
    if user_oid in group.get("members", []):
        return group_repository.format_group_id(group)

    # 3. Thêm vào danh sách chờ duyệt (pending_members) thay vì thêm trực tiếp vào members
    group_id = str(group["_id"])
    await group_repository.add_pending_member(
        group_id=group_id,
        user_id=current_user["id"],
        email=current_user["email"],
        full_name=current_user.get("full_name", "")
    )

    # 4. Gửi thông báo cho chủ nhóm
    await notification_repository.create_notification(
        user_id=str(group["created_by"]),
        message=f"Người dùng {current_user.get('email')} ({current_user.get('full_name', '')}) đã yêu cầu tham gia nhóm '{group['name']}' qua link mời."
    )

    updated_group = await group_repository.find_by_id(group_id)
    return group_repository.format_group_id(updated_group)


@router.post(
    "/{group_id}/approve/{user_id}",
    response_model=GroupResponse,
    status_code=status.HTTP_200_OK,
    summary="Phê duyệt yêu cầu tham gia nhóm",
)
async def approve_join_request(
    group_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    group = await group_repository.find_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nhóm học tập không tồn tại."
        )

    # Chỉ chủ nhóm (created_by) mới được phê duyệt
    if str(group["created_by"]) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ chủ nhóm mới có quyền phê duyệt yêu cầu tham gia."
        )

    # Kiểm tra xem user_id có trong danh sách chờ duyệt không
    pending_ids = [pm["user_id"] for pm in group.get("pending_members", [])]
    if user_id not in pending_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Người dùng này không có yêu cầu tham gia chờ duyệt."
        )

    # 1. Thêm vào thành viên chính thức
    await group_repository.add_member(group_id, user_id)
    # 2. Xóa khỏi danh sách chờ duyệt
    await group_repository.remove_pending_member(group_id, user_id)

    # 3. Gửi thông báo cho người dùng được phê duyệt
    await notification_repository.create_notification(
        user_id=user_id,
        message=f"Yêu cầu tham gia nhóm học tập '{group['name']}' của bạn đã được chủ nhóm phê duyệt!"
    )

    updated_group = await group_repository.find_by_id(group_id)
    return group_repository.format_group_id(updated_group)


@router.post(
    "/{group_id}/reject/{user_id}",
    response_model=GroupResponse,
    status_code=status.HTTP_200_OK,
    summary="Từ chối yêu cầu tham gia nhóm",
)
async def reject_join_request(
    group_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    group = await group_repository.find_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nhóm học tập không tồn tại."
        )

    # Chỉ chủ nhóm mới được từ chối
    if str(group["created_by"]) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ chủ nhóm mới có quyền từ chối yêu cầu tham gia."
        )

    # Kiểm tra xem user_id có trong danh sách chờ duyệt không
    pending_ids = [pm["user_id"] for pm in group.get("pending_members", [])]
    if user_id not in pending_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Người dùng này không có yêu cầu tham gia chờ duyệt."
        )

    # 1. Xóa khỏi danh sách chờ duyệt
    await group_repository.remove_pending_member(group_id, user_id)

    # 2. Gửi thông báo cho người dùng bị từ chối
    await notification_repository.create_notification(
        user_id=user_id,
        message=f"Yêu cầu tham gia nhóm học tập '{group['name']}' của bạn đã bị từ chối."
    )

    updated_group = await group_repository.find_by_id(group_id)
    return group_repository.format_group_id(updated_group)


@router.post(
    "/{group_id}/members",
    response_model=GroupResponse,
    status_code=status.HTTP_200_OK,
    summary="Mời thành viên mới vào nhóm học tập bằng Email",
)
async def add_group_member(
    group_id: str,
    request: GroupMemberRequest,
    current_user: dict = Depends(get_current_user)
):
    # 1. Tìm nhóm
    group = await group_repository.find_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nhóm học tập không tồn tại."
        )

    # 2. Kiểm tra phân quyền (chỉ members hoặc owner mới được mời thành viên mới)
    user_oid = ObjectId(current_user["id"])
    if user_oid not in group["members"] and group["created_by"] != user_oid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền mời thành viên vào nhóm này."
        )

    # 3. Tìm thành viên bằng email
    invited_user = await users_collection.find_one({"email": request.email})
    if not invited_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy người dùng có email này."
        )

    invited_user_id = str(invited_user["_id"])
    
    # 4. Thêm vào nhóm
    success = await group_repository.add_member(group_id, invited_user_id)
    
    # 5. Gửi thông báo cho thành viên được mời
    await notification_repository.create_notification(
        user_id=invited_user_id,
        message=f"Bạn đã được mời tham gia nhóm học tập '{group['name']}' bởi {current_user.get('email')}."
    )

    updated_group = await group_repository.find_by_id(group_id)
    return group_repository.format_group_id(updated_group)


@router.delete(
    "/{group_id}/members/{member_id}",
    response_model=GroupResponse,
    status_code=status.HTTP_200_OK,
    summary="Xóa hoặc rời khỏi nhóm học tập",
)
async def remove_group_member(
    group_id: str,
    member_id: str,
    current_user: dict = Depends(get_current_user)
):
    group = await group_repository.find_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nhóm học tập không tồn tại."
        )

    # Phân quyền: Chỉ chủ nhóm được xóa người khác, hoặc thành viên tự rời nhóm
    if current_user["id"] != str(group["created_by"]) and current_user["id"] != member_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền thực hiện thao tác xóa thành viên này."
        )

    success = await group_repository.remove_member(group_id, member_id)
    
    # Gửi thông báo
    await notification_repository.create_notification(
        user_id=member_id,
        message=f"Bạn đã rời khỏi hoặc bị xóa khỏi nhóm học tập '{group['name']}'."
    )

    updated_group = await group_repository.find_by_id(group_id)
    return group_repository.format_group_id(updated_group)


@router.get(
    "/{group_id}/resources",
    summary="Lấy danh sách tài liệu và thư mục được chia sẻ cho nhóm học tập",
)
async def get_group_resources(
    group_id: str,
    current_user: dict = Depends(get_current_user)
):
    # 1. Kiểm tra nhóm tồn tại
    group = await group_repository.find_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nhóm học tập không tồn tại."
        )

    # 2. Kiểm tra quyền thành viên
    member_ids = [str(m) for m in group.get("members", [])]
    if current_user["id"] not in member_ids and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không phải thành viên của nhóm học tập này."
        )

    # 3. Lấy tất cả permissions có share_type='group' của group này
    from bson import ObjectId
    perms = await database["permissions"].find({
        "share_type": "group",
        "user_id": ObjectId(group_id)
    }).to_list(length=1000)

    folder_ids = [p["resource_id"] for p in perms if p["resource_type"] == "folder"]
    doc_ids = [p["resource_id"] for p in perms if p["resource_type"] == "document"]

    # 4. Truy vấn thông tin chi tiết các thư mục và tài liệu con đang hoạt động
    from app.repositories import folder_repository, document_repository

    folders = []
    if folder_ids:
        folders = await database["folders"].find({
            "_id": {"$in": folder_ids},
            "is_deleted": False
        }).to_list(length=1000)

    docs = []
    if doc_ids:
        docs = await database["documents"].find({
            "_id": {"$in": doc_ids},
            "is_deleted": False
        }).to_list(length=1000)

    return {
        "folders": [folder_repository.format_folder_id(f) for f in folders],
        "documents": [document_repository.format_document_id(d) for d in docs]
    }


@router.patch(
    "/{group_id}",
    response_model=GroupResponse,
    status_code=status.HTTP_200_OK,
    summary="Chỉnh sửa thông tin nhóm học tập (Tên, Mô tả)",
)
async def update_group_details(
    group_id: str,
    request: GroupUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    group = await group_repository.find_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nhóm học tập không tồn tại."
        )

    # Chỉ chủ nhóm hoặc Admin mới được đổi tên/mô tả nhóm
    if str(group["created_by"]) != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ chủ nhóm mới có quyền chỉnh sửa thông tin nhóm."
        )

    updated = await group_repository.update_group(
        group_id=group_id,
        name=request.name,
        description=request.description
    )
    return group_repository.format_group_id(updated)


@router.delete(
    "/{group_id}",
    status_code=status.HTTP_200_OK,
    summary="Xóa nhóm học tập",
)
async def delete_existing_group(
    group_id: str,
    current_user: dict = Depends(get_current_user)
):
    group = await group_repository.find_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nhóm học tập không tồn tại."
        )

    # Chỉ chủ nhóm hoặc Admin mới được xóa nhóm
    if str(group["created_by"]) != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ chủ nhóm mới có quyền giải tán/xóa nhóm học tập."
        )

    success = await group_repository.delete_group(group_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể xóa nhóm học tập. Vui lòng thử lại."
        )
    return {"message": f"Đã xóa nhóm học tập '{group['name']}' thành công."}


