"""
repositories/document_repository.py
===================================
Mô tả:
    Data Access Layer cho Document — tất cả câu query MongoDB liên quan đến Document.
    Hỗ trợ đầy đủ cơ chế xóa mềm (Soft Delete) và quản lý thùng rác cấp doanh nghiệp.
"""

from typing import Optional, List
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from app.database.connection import database
from app.models.document import create_document_document

# Lấy collection "documents" từ database
documents_collection = database["documents"]


async def create_indexes() -> None:
    """
    Tạo indexes cho documents collection để tối ưu hóa tốc độ truy vấn và tìm kiếm.
    """
    # Index phục vụ cho việc liệt kê tài liệu trong thư mục
    await documents_collection.create_index([("folder_id", 1), ("is_deleted", 1)])
    # Index phục vụ tìm kiếm nhanh theo tên file
    await documents_collection.create_index([("name", "text")])


async def create_document(
    name: str,
    folder_id: Optional[str],
    storage_path: str,
    file_size: int,
    mime_type: str,
    created_by: str,
    current_version: int = 1,
    description: str = "",
    tags: list = [],
) -> dict:
    """
    Tạo một document metadata mới trong MongoDB.

    Args:
        name:            Tên file hiển thị
        folder_id:       ID thư mục cha (string hoặc None)
        storage_path:    Đường dẫn lưu trên Supabase Storage
        file_size:       Kích thước file (bytes)
        mime_type:       MIME-type của file
        created_by:      ID người tạo/tải lên (string)
        current_version: Phiên bản đầu tiên (mặc định: 1)
        description:     Mô tả ngắn gọn về file
        tags:            Danh sách các nhãn phân loại

    Returns:
        dict: Document metadata vừa tạo đầy đủ thông tin kèm _id
    """
    doc_data = create_document_document(
        name=name,
        folder_id=folder_id,
        storage_path=storage_path,
        file_size=file_size,
        mime_type=mime_type,
        created_by=created_by,
        current_version=current_version,
        description=description,
        tags=tags,
    )

    result = await documents_collection.insert_one(doc_data)
    created_doc = await documents_collection.find_one({"_id": result.inserted_id})
    return created_doc


async def find_by_id(doc_id: str, include_deleted: bool = False) -> Optional[dict]:
    """
    Tìm tài liệu theo ID.
    """
    try:
        oid = ObjectId(doc_id)
    except InvalidId:
        return None

    query = {"_id": oid}
    if not include_deleted:
        query["is_deleted"] = False

    return await documents_collection.find_one(query)


async def find_by_folder(folder_id: Optional[str], include_deleted: bool = False) -> List[dict]:
    """
    Lấy danh sách tài liệu trong một thư mục cụ thể (hoặc thư mục gốc).
    """
    folder_oid = ObjectId(folder_id) if folder_id else None
    
    query = {"folder_id": folder_oid}
    if not include_deleted:
        query["is_deleted"] = False

    cursor = documents_collection.find(query).sort("name", 1)
    
    docs = []
    async for doc in cursor:
        docs.append(doc)
    return docs


async def search_documents(
    query: str, 
    folder_id: Optional[str] = None, 
    include_deleted: bool = False
) -> List[dict]:
    """
    Tìm kiếm tài liệu theo tên và lọc theo thư mục (nếu có).
    """
    filter_query = {}
    if not include_deleted:
        filter_query["is_deleted"] = False
        
    if query.strip():
        # Lọc theo tên chứa từ khóa (regex không phân biệt hoa thường)
        filter_query["name"] = {"$regex": query.strip(), "$options": "i"}

    if folder_id:
        try:
            filter_query["folder_id"] = ObjectId(folder_id)
        except InvalidId:
            return []

    cursor = documents_collection.find(filter_query).sort("name", 1)
    
    docs = []
    async for doc in cursor:
        docs.append(doc)
    return docs


async def update_document(doc_id: str, update_data: dict) -> Optional[dict]:
    """
    Cập nhật linh hoạt thông tin tài liệu (Đổi tên, sửa mô tả, đổi version, di chuyển folder).
    """
    try:
        oid = ObjectId(doc_id)
    except InvalidId:
        return None

    # Chuẩn hóa folder_id nếu có cập nhật di chuyển thư mục
    if "folder_id" in update_data:
        f_id = update_data["folder_id"]
        update_data["folder_id"] = ObjectId(f_id) if f_id else None

    # Luôn ghi nhận mốc thời gian cập nhật mới nhất
    update_data["updated_at"] = datetime.now(timezone.utc)

    await documents_collection.update_one(
        {"_id": oid},
        {"$set": update_data}
    )

    return await documents_collection.find_one({"_id": oid})


async def rename_document(doc_id: str, name: str) -> Optional[dict]:
    """
    Đổi tên hiển thị của tài liệu (Giữ nguyên để tương thích ngược).
    """
    return await update_document(doc_id, {"name": name})


async def soft_delete_document(doc_id: str) -> bool:
    """
    Xóa mềm tài liệu đưa vào thùng rác.
    """
    try:
        oid = ObjectId(doc_id)
    except InvalidId:
        return False

    update_data = {
        "is_deleted": True,
        "deleted_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    result = await documents_collection.update_one(
        {"_id": oid, "is_deleted": False},
        {"$set": update_data}
    )
    return result.modified_count > 0


async def restore_document(doc_id: str) -> bool:
    """
    Khôi phục tài liệu đã bị xóa mềm khỏi thùng rác.
    """
    try:
        oid = ObjectId(doc_id)
    except InvalidId:
        return False

    update_data = {
        "is_deleted": False,
        "deleted_at": None,
        "updated_at": datetime.now(timezone.utc)
    }

    result = await documents_collection.update_one(
        {"_id": oid, "is_deleted": True},
        {"$set": update_data}
    )
    return result.modified_count > 0


async def find_deleted_documents(created_by: str) -> List[dict]:
    """
    Lấy danh sách tài liệu bị xóa mềm của người dùng.
    """
    try:
        user_oid = ObjectId(created_by)
    except InvalidId:
        return []

    query = {
        "created_by": user_oid,
        "is_deleted": True
    }
    cursor = documents_collection.find(query).sort("deleted_at", -1)
    
    docs = []
    async for doc in cursor:
        docs.append(doc)
    return docs


async def hard_delete_document(doc_id: str) -> bool:
    """
    Xóa cứng vĩnh viễn tài liệu khỏi MongoDB.
    """
    try:
        oid = ObjectId(doc_id)
    except InvalidId:
        return False

    result = await documents_collection.delete_one({"_id": oid})
    return result.deleted_count > 0


async def delete_document(doc_id: str) -> bool:
    """
    Wrapper giữ nguyên tương thích ngược cho hàm delete_document cũ.
    """
    return await hard_delete_document(doc_id)


def format_document_id(doc: dict) -> dict:
    """
    Helper: convert MongoDB ObjectId sang string để trả về JSON.
    """
    doc_copy = dict(doc)

    if "_id" in doc_copy:
        doc_copy["id"] = str(doc_copy.pop("_id"))

    if "folder_id" in doc_copy and doc_copy["folder_id"] is not None:
        doc_copy["folder_id"] = str(doc_copy["folder_id"])

    if "created_by" in doc_copy and doc_copy["created_by"] is not None:
        doc_copy["created_by"] = str(doc_copy["created_by"])

    if "tags" not in doc_copy or doc_copy["tags"] is None:
        doc_copy["tags"] = []

    return doc_copy
