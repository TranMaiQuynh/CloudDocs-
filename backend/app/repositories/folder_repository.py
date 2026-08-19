"""
repositories/folder_repository.py
=================================
Mô tả:
    Data Access Layer cho Folder — quản trị các truy vấn MongoDB liên quan đến Folder.
    Hỗ trợ đầy đủ cơ chế xóa mềm (Soft Delete) và quản lý thùng rác cấp doanh nghiệp.
"""

from typing import Optional, List
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from app.database.connection import database
from app.models.folder import create_folder_document

# Lấy collection "folders" từ database
folders_collection = database["folders"]


async def create_indexes() -> None:
    """
    Tạo indexes cho folders collection để tối ưu hóa tốc độ truy vấn.
    """
    # Index tìm kiếm theo thư mục cha & trạng thái hoạt động (dùng nhiều khi duyệt cây thư mục)
    await folders_collection.create_index([("parent_id", 1), ("is_deleted", 1)])
    # Index phục vụ cho việc kiểm tra trùng tên thư mục cùng cấp
    await folders_collection.create_index([("name", 1), ("parent_id", 1), ("is_deleted", 1)])


async def create_folder(
    name: str,
    parent_id: Optional[str] = None,
    created_by: str = "",
    description: str = "",
    tags: list = [],
) -> dict:
    """
    Tạo thư mục mới trong MongoDB.

    Args:
        name:        Tên thư mục
        parent_id:   ID của thư mục cha (string hoặc None)
        created_by:  ID của người tạo thư mục (string)
        description: Mô tả ngắn gọn về thư mục
        tags:        Danh sách nhãn dán

    Returns:
        dict: Thư mục vừa tạo đầy đủ thông tin (bao gồm cả _id)
    """
    folder_doc = create_folder_document(
        name=name,
        parent_id=parent_id,
        created_by=created_by,
        description=description,
        tags=tags,
    )

    result = await folders_collection.insert_one(folder_doc)
    created_folder = await folders_collection.find_one({"_id": result.inserted_id})
    return created_folder


async def find_by_id(folder_id: str, include_deleted: bool = False) -> Optional[dict]:
    """
    Tìm thư mục theo MongoDB ObjectId.

    Args:
        folder_id:       ID của thư mục cần tìm
        include_deleted: True nếu muốn tìm cả thư mục đã xóa mềm (nằm trong thùng rác)

    Returns:
        dict | None: Tài liệu thư mục nếu tìm thấy
    """
    try:
        oid = ObjectId(folder_id)
    except InvalidId:
        return None

    query = {"_id": oid}
    if not include_deleted:
        query["is_deleted"] = False

    return await folders_collection.find_one(query)


async def find_by_name_and_parent(
    name: str, 
    parent_id: Optional[str] = None, 
    include_deleted: bool = False
) -> Optional[dict]:
    """
    Tìm thư mục theo tên và thư mục cha (thường dùng để validate trùng tên thư mục cùng cấp).
    """
    parent_oid = ObjectId(parent_id) if parent_id else None
    
    query = {
        "name": name.strip(),
        "parent_id": parent_oid
    }
    if not include_deleted:
        query["is_deleted"] = False

    return await folders_collection.find_one(query)


async def find_subfolders(
    parent_id: Optional[str] = None, 
    include_deleted: bool = False
) -> List[dict]:
    """
    Lấy danh sách các thư mục con trực thuộc một thư mục cha (hoặc ở thư mục gốc).

    Args:
        parent_id:       ID thư mục cha (None nếu lấy ở Root)
        include_deleted: True nếu muốn lấy cả các thư mục con đã xóa mềm

    Returns:
        List[dict]: Danh sách thư mục con, sắp xếp theo thứ tự bảng chữ cái
    """
    parent_oid = ObjectId(parent_id) if parent_id else None
    
    query = {"parent_id": parent_oid}
    if not include_deleted:
        query["is_deleted"] = False

    cursor = folders_collection.find(query).sort("name", 1)
    
    folders = []
    async for doc in cursor:
        folders.append(doc)
    return folders


async def update_folder(folder_id: str, update_data: dict) -> Optional[dict]:
    """
    Cập nhật linh hoạt thông tin thư mục (Đổi tên, sửa mô tả, di chuyển vị trí cha).

    Args:
        folder_id:   ID thư mục cần cập nhật
        update_data: Dict chứa các trường cần thay đổi (ví dụ: {"name": "Tên mới", "parent_id": oid})

    Returns:
        dict | None: Dữ liệu thư mục sau khi cập nhật
    """
    try:
        oid = ObjectId(folder_id)
    except InvalidId:
        return None

    # Chuẩn hóa parent_id nếu có cập nhật di chuyển thư mục
    if "parent_id" in update_data:
        p_id = update_data["parent_id"]
        update_data["parent_id"] = ObjectId(p_id) if p_id else None

    # Luôn ghi nhận mốc thời gian cập nhật mới nhất
    update_data["updated_at"] = datetime.now(timezone.utc)

    await folders_collection.update_one(
        {"_id": oid},
        {"$set": update_data}
    )

    return await folders_collection.find_one({"_id": oid})


async def soft_delete_folder(folder_id: str) -> bool:
    """
    Xóa mềm (Soft Delete) một thư mục. Chuyển thư mục vào thùng rác.

    Args:
        folder_id: ID thư mục cần xóa mềm

    Returns:
        bool: True nếu thao tác cập nhật thành công
    """
    try:
        oid = ObjectId(folder_id)
    except InvalidId:
        return False

    update_data = {
        "is_deleted": True,
        "deleted_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    result = await folders_collection.update_one(
        {"_id": oid, "is_deleted": False},
        {"$set": update_data}
    )
    return result.modified_count > 0


async def restore_folder(folder_id: str) -> bool:
    """
    Khôi phục thư mục đã bị xóa mềm khỏi thùng rác.

    Args:
        folder_id: ID thư mục cần khôi phục

    Returns:
        bool: True nếu khôi phục thành công
    """
    try:
        oid = ObjectId(folder_id)
    except InvalidId:
        return False

    update_data = {
        "is_deleted": False,
        "deleted_at": None,
        "updated_at": datetime.now(timezone.utc)
    }

    result = await folders_collection.update_one(
        {"_id": oid, "is_deleted": True},
        {"$set": update_data}
    )
    return result.modified_count > 0


async def find_deleted_folders(created_by: str) -> List[dict]:
    """
    Lấy danh sách tất cả thư mục đã bị xóa mềm (nằm trong thùng rác) của người dùng.
    """
    try:
        user_oid = ObjectId(created_by)
    except InvalidId:
        return []

    query = {
        "created_by": user_oid,
        "is_deleted": True
    }
    cursor = folders_collection.find(query).sort("deleted_at", -1) # Mới xóa xếp lên đầu
    
    folders = []
    async for doc in cursor:
        folders.append(doc)
    return folders


async def hard_delete_folder(folder_id: str) -> bool:
    """
    Xóa cứng vĩnh viễn thư mục khỏi cơ sở dữ liệu MongoDB.

    Args:
        folder_id: ID thư mục cần xóa vĩnh viễn

    Returns:
        bool: True nếu xóa thành công
    """
    try:
        oid = ObjectId(folder_id)
    except InvalidId:
        return False

    result = await folders_collection.delete_one({"_id": oid})
    return result.deleted_count > 0


def format_folder_id(folder: dict) -> dict:
    """
    Helper: Chuyển đổi ObjectId sang string để trả về định dạng JSON rest api.
    """
    folder_copy = dict(folder)
    
    if "_id" in folder_copy:
        folder_copy["id"] = str(folder_copy.pop("_id"))
        
    if "parent_id" in folder_copy and folder_copy["parent_id"] is not None:
        folder_copy["parent_id"] = str(folder_copy["parent_id"])
        
    if "created_by" in folder_copy and folder_copy["created_by"] is not None:
        folder_copy["created_by"] = str(folder_copy["created_by"])
        
    if "tags" not in folder_copy or folder_copy["tags"] is None:
        folder_copy["tags"] = []
        
    return folder_copy
