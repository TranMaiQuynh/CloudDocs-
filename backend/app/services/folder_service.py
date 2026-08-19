"""
services/folder_service.py
==========================
Mô tả:
    Business Logic Layer cho Folder.
    Thực hiện kiểm tra điều kiện nghiệp vụ, kiểm tra quyền truy cập đệ quy và xử lý đệ quy (Soft Delete / Restore).
"""

from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import HTTPException, status
from app.repositories import folder_repository, activity_repository
from app.schemas.folder_schema import FolderCreateRequest, FolderUpdateRequest
from app.database.connection import database
from app.services.permission_service import check_user_access, AccessLevel

# Dùng direct database collections cho thao tác đệ quy
folders_collection = database["folders"]
documents_collection = database["documents"]
permissions_collection = database["permissions"]
users_collection = database["users"]


async def create_folder(request: FolderCreateRequest, created_by: str) -> dict:
    """
    Tạo thư mục mới.
    Kiểm tra:
    - Thư mục cha phải tồn tại (nếu parent_id khác None).
    - Người tạo phải có quyền ghi (Editor) trên thư mục cha.
    - Tên thư mục không được trùng lặp trong cùng thư mục cha.
    """
    if request.parent_id:
        parent = await folder_repository.find_by_id(request.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thư mục cha không tồn tại hoặc đã bị xóa mềm."
            )
        
        # Kiểm tra quyền ghi trên thư mục cha
        has_write = await check_user_access(created_by, request.parent_id, "folder", AccessLevel.EDITOR)
        if not has_write:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền tạo thư mục mới bên trong thư mục cha này."
            )
    else:
        # Cho phép bất kỳ người dùng nào tạo thư mục ở gốc (root)
        pass

    existing = await folder_repository.find_by_name_and_parent(request.name, request.parent_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tên thư mục đã tồn tại trong thư mục cha này. Vui lòng chọn tên khác."
        )

    new_folder = await folder_repository.create_folder(
        name=request.name,
        parent_id=request.parent_id,
        created_by=created_by,
        description=request.description or "",
        tags=request.tags or [],
    )
    
    # Ghi nhận nhật ký hoạt động
    user = await users_collection.find_one({"_id": ObjectId(created_by)}, {"full_name": 1})
    user_name = user.get("full_name") if user else "Học viên"
    await activity_repository.create_activity(
        user_id=created_by,
        user_name=user_name,
        action="CREATE_FOLDER",
        resource_name=request.name,
        details=f"Đã tạo thư mục mới '{request.name}'."
    )
    return folder_repository.format_folder_id(new_folder)


async def get_folder_by_id(folder_id: str, user_id: str) -> dict:
    """
    Lấy thông tin thư mục theo ID (bỏ qua nếu đã bị xóa mềm).
    Yêu cầu quyền đọc (Viewer).
    """
    # 1. Kiểm tra quyền truy cập trước
    has_read = await check_user_access(user_id, folder_id, "folder", AccessLevel.VIEWER)
    if not has_read:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập vào thư mục này."
        )

    folder = await folder_repository.find_by_id(folder_id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thư mục không tồn tại hoặc đã bị xóa mềm."
        )
    return folder_repository.format_folder_id(folder)


async def list_folders(parent_id: Optional[str], user_id: str) -> List[dict]:
    """
    Lấy danh sách các thư mục con đang hoạt động (is_deleted = False).
    Yêu cầu quyền đọc (Viewer).
    """
    # 1. Nếu tìm kiếm trong thư mục cha cụ thể
    if parent_id:
        parent = await folder_repository.find_by_id(parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thư mục cha không tồn tại hoặc đã bị xóa mềm."
            )
        
        # Kiểm tra quyền đọc trên thư mục cha
        has_read = await check_user_access(user_id, parent_id, "folder", AccessLevel.VIEWER)
        if not has_read:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền truy cập thư mục này."
            )

        folders = await folder_repository.find_subfolders(parent_id, include_deleted=False)
        return [folder_repository.format_folder_id(f) for f in folders]

    # 2. Nếu ở thư mục gốc (parent_id = None), lấy những gì thuộc sở hữu hoặc được chia sẻ
    else:
        # Lấy tất cả thư mục gốc hoạt động
        all_root_folders = await folders_collection.find({"parent_id": None, "is_deleted": False}).to_list(length=500)
        
        # Lọc ra những thư mục mà user có quyền truy cập
        user_folders = []
        for f in all_root_folders:
            f_id = str(f["_id"])
            
            # Nếu thư mục này được chia sẻ cho bất kỳ nhóm nào, không hiện ở Trang chủ (Tài liệu của tôi)
            is_group_shared = await database["permissions"].find_one({
                "resource_id": f["_id"],
                "resource_type": "folder",
                "share_type": "group"
            })
            if is_group_shared:
                continue
                
            if str(f.get("created_by")) == user_id:
                user_folders.append(f)
            else:
                # Kiểm tra xem có quyền chia sẻ không (Bỏ qua link chia sẻ công khai)
                has_access = await check_user_access(user_id, f_id, "folder", AccessLevel.VIEWER, allow_link_sharing=False)
                if has_access:
                    user_folders.append(f)

        return [folder_repository.format_folder_id(f) for f in user_folders]


async def rename_folder(folder_id: str, request: FolderUpdateRequest, user_id: str) -> dict:
    """
    Cập nhật thông tin thư mục (Đổi tên, sửa mô tả, hoặc di chuyển vị trí).
    Yêu cầu quyền ghi (Editor).
    """
    # Kiểm tra quyền ghi
    has_write = await check_user_access(user_id, folder_id, "folder", AccessLevel.EDITOR)
    if not has_write:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền cập nhật thư mục này."
        )

    folder = await folder_repository.find_by_id(folder_id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thư mục không tồn tại hoặc đã bị xóa mềm."
        )

    update_payload = {}

    # 1. Xử lý đổi tên và kiểm tra trùng tên cùng cấp
    if request.name is not None:
        target_name = request.name.strip()
        parent_id = str(folder["parent_id"]) if folder.get("parent_id") else None

        existing = await folder_repository.find_by_name_and_parent(target_name, parent_id)
        if existing and str(existing["_id"]) != folder_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tên thư mục đã tồn tại ở cấp độ này. Vui lòng chọn tên khác."
            )
        update_payload["name"] = target_name

    # 2. Xử lý sửa mô tả
    if request.description is not None:
        update_payload["description"] = request.description.strip()

    # 3. Xử lý di chuyển thư mục cha (parent_id)
    if request.parent_id is not None:
        if request.parent_id == folder_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể đặt thư mục cha là chính nó."
            )
        if request.parent_id != "":
            # Kiểm tra quyền ghi trên thư mục cha mới
            new_parent_has_write = await check_user_access(user_id, request.parent_id, "folder", AccessLevel.EDITOR)
            if not new_parent_has_write:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bạn không có quyền di chuyển thư mục vào thư mục đích này."
                )

            new_parent = await folder_repository.find_by_id(request.parent_id)
            if not new_parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Thư mục cha mới không tồn tại hoặc đã bị xóa."
                )
            update_payload["parent_id"] = request.parent_id
        else:
            update_payload["parent_id"] = None

    # 4. Xử lý cập nhật nhãn dán (tags)
    if request.tags is not None:
        update_payload["tags"] = request.tags

    if not update_payload:
        return folder_repository.format_folder_id(folder)

    updated_folder = await folder_repository.update_folder(folder_id, update_payload)
    
    # Ghi nhận nhật ký hoạt động
    user = await users_collection.find_one({"_id": ObjectId(user_id)}, {"full_name": 1})
    user_name = user.get("full_name") if user else "Học viên"
    details = []
    if "name" in update_payload:
        details.append(f"đổi tên thành '{update_payload['name']}'")
    if "description" in update_payload:
        details.append(f"cập nhật mô tả")
    if "tags" in update_payload:
        details.append(f"cập nhật nhãn ({', '.join(update_payload['tags'])})")
    if "parent_id" in update_payload:
        details.append(f"di chuyển vào thư mục ID {update_payload['parent_id']}")
    await activity_repository.create_activity(
        user_id=user_id,
        user_name=user_name,
        action="UPDATE_FOLDER",
        resource_name=folder["name"],
        details=f"Đã cập nhật thư mục '{folder['name']}': {', '.join(details)}."
    )
    return folder_repository.format_folder_id(updated_folder)


async def delete_folder(folder_id: str, user_id: str) -> dict:
    """
    Xóa mềm (Soft Delete) thư mục và đệ quy toàn bộ nội dung con của nó.
    Yêu cầu quyền ghi (Editor).
    """
    # Kiểm tra quyền ghi
    has_write = await check_user_access(user_id, folder_id, "folder", AccessLevel.EDITOR)
    if not has_write:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xóa thư mục này."
        )

    folder = await folder_repository.find_by_id(folder_id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thư mục không tồn tại hoặc đã bị xóa."
        )

    # Thực hiện xóa mềm đệ quy thư mục và tài liệu con
    await _soft_delete_recursive(folder_id)

    # Ghi nhận nhật ký hoạt động
    user = await users_collection.find_one({"_id": ObjectId(user_id)}, {"full_name": 1})
    user_name = user.get("full_name") if user else "Học viên"
    await activity_repository.create_activity(
        user_id=user_id,
        user_name=user_name,
        action="DELETE_FOLDER",
        resource_name=folder["name"],
        details=f"Đã di chuyển thư mục '{folder['name']}' và toàn bộ con đệ quy vào thùng rác."
    )

    return {
        "success": True,
        "message": f"Thư mục '{folder['name']}' và toàn bộ nội dung đã được đưa vào thùng rác."
    }


async def _soft_delete_recursive(folder_id: str) -> None:
    """
    Hàm helper đệ quy xóa mềm toàn bộ cây thư mục con và tài liệu con.
    """
    now = datetime.now(timezone.utc)
    folder_oid = ObjectId(folder_id)

    # 1. Xóa mềm thư mục hiện tại
    await folder_repository.soft_delete_folder(folder_id)

    # 2. Xóa mềm tất cả tài liệu con trực tiếp nằm trong thư mục này
    await documents_collection.update_many(
        {"folder_id": folder_oid, "is_deleted": False},
        {"$set": {"is_deleted": True, "deleted_at": now, "updated_at": now}}
    )

    # 3. Quét tất cả thư mục con để gọi đệ quy
    subfolders = await folder_repository.find_subfolders(folder_id, include_deleted=False)
    for sub in subfolders:
        await _soft_delete_recursive(str(sub["_id"]))


async def restore_folder(folder_id: str, user_id: str) -> dict:
    """
    Khôi phục thư mục đã bị xóa mềm và toàn bộ các tệp tin/thư mục con đệ quy.
    Yêu cầu quyền ghi (Editor) trên thư mục đó.
    """
    # Kiểm tra quyền ghi
    has_write = await check_user_access(user_id, folder_id, "folder", AccessLevel.EDITOR)
    if not has_write:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền khôi phục thư mục này."
        )

    folder = await folder_repository.find_by_id(folder_id, include_deleted=True)
    if not folder or not folder.get("is_deleted"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thư mục không tồn tại trong thùng rác."
        )

    # Khôi phục đệ quy
    await _restore_recursive(folder_id)

    # Ghi nhận nhật ký hoạt động
    user = await users_collection.find_one({"_id": ObjectId(user_id)}, {"full_name": 1})
    user_name = user.get("full_name") if user else "Học viên"
    await activity_repository.create_activity(
        user_id=user_id,
        user_name=user_name,
        action="RESTORE_FOLDER",
        resource_name=folder["name"],
        details=f"Đã khôi phục thư mục '{folder['name']}' và toàn bộ con đệ quy từ thùng rác."
    )

    return {
        "success": True,
        "message": f"Đã khôi phục thành công thư mục '{folder['name']}' và nội dung con."
    }


async def _restore_recursive(folder_id: str) -> None:
    """
    Hàm helper đệ quy khôi phục toàn bộ cây thư mục con và tài liệu con.
    """
    now = datetime.now(timezone.utc)
    folder_oid = ObjectId(folder_id)

    # 1. Khôi phục thư mục hiện tại
    await folder_repository.restore_folder(folder_id)

    # 2. Khôi phục tài liệu con trực tiếp nằm trong thư mục này
    await documents_collection.update_many(
        {"folder_id": folder_oid, "is_deleted": True},
        {"$set": {"is_deleted": False, "deleted_at": None, "updated_at": now}}
    )

    # 3. Quét tất cả thư mục con (bao gồm cả đã xóa mềm) để gọi đệ quy khôi phục
    subfolders = await folder_repository.find_subfolders(folder_id, include_deleted=True)
    for sub in subfolders:
        if sub.get("is_deleted"):
            await _restore_recursive(str(sub["_id"]))


async def list_trash_folders(user_id: str) -> List[dict]:
    """
    Lấy danh sách thư mục đã bị xóa mềm của người dùng.
    """
    folders = await folder_repository.find_deleted_folders(user_id)
    return [folder_repository.format_folder_id(f) for f in folders]
