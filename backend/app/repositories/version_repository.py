"""
repositories/version_repository.py
==================================
Mô tả:
    Data Access Layer cho Version — quản trị lịch sử phiên bản tài liệu trên MongoDB.
"""

from typing import Optional, List
from bson import ObjectId
from bson.errors import InvalidId
from app.database.connection import database
from app.models.version import create_version_document

# Lấy collection "versions" từ database
versions_collection = database["versions"]


async def create_indexes() -> None:
    """
    Tạo indexes cho versions collection để tối ưu hóa tốc độ truy vấn.
    """
    # Index tìm kiếm danh sách phiên bản thuộc tài liệu
    await versions_collection.create_index([("document_id", 1), ("version_number", -1)])


async def create_version(
    document_id: str,
    version_number: int,
    storage_path: str,
    file_size: int,
    created_by: str,
    change_log: str = "",
) -> dict:
    """
    Tạo một bản ghi phiên bản mới trong MongoDB.

    Args:
        document_id:    ID tài liệu gốc
        version_number: Số thứ tự phiên bản (1, 2, 3...)
        storage_path:   Đường dẫn vật lý trên Supabase Storage
        file_size:      Kích thước phiên bản (bytes)
        created_by:     ID người tải lên phiên bản này
        change_log:     Mô tả các thay đổi của phiên bản

    Returns:
        dict: Bản ghi phiên bản vừa tạo
    """
    version_doc = create_version_document(
        document_id=document_id,
        version_number=version_number,
        storage_path=storage_path,
        file_size=file_size,
        created_by=created_by,
        change_log=change_log,
    )

    result = await versions_collection.insert_one(version_doc)
    created_version = await versions_collection.find_one({"_id": result.inserted_id})
    return created_version


async def find_by_document(document_id: str) -> List[dict]:
    """
    Lấy toàn bộ danh sách phiên bản của một tài liệu.

    Returns:
        List[dict]: Sắp xếp theo phiên bản mới nhất lên đầu.
    """
    try:
        doc_oid = ObjectId(document_id)
    except InvalidId:
        return []

    cursor = versions_collection.find({"document_id": doc_oid}).sort("version_number", -1)
    
    versions = []
    async for doc in cursor:
        versions.append(doc)
    return versions


async def find_by_document_and_number(document_id: str, version_number: int) -> Optional[dict]:
    """
    Lấy thông tin một phiên bản cụ thể dựa trên ID tài liệu và số phiên bản.
    """
    try:
        doc_oid = ObjectId(document_id)
    except InvalidId:
        return None

    query = {
        "document_id": doc_oid,
        "version_number": version_number
    }
    return await versions_collection.find_one(query)


async def delete_all_by_document(document_id: str) -> int:
    """
    Xóa toàn bộ các bản ghi phiên bản của một tài liệu (Khi thực hiện xóa cứng tài liệu).
    """
    try:
        doc_oid = ObjectId(document_id)
    except InvalidId:
        return 0

    result = await versions_collection.delete_many({"document_id": doc_oid})
    return result.deleted_count


async def delete_specific_version(document_id: str, version_number: int) -> bool:
    """
    Xóa một bản ghi phiên bản cũ cụ thể.
    """
    try:
        doc_oid = ObjectId(document_id)
    except InvalidId:
        return False

    query = {
        "document_id": doc_oid,
        "version_number": version_number
    }
    result = await versions_collection.delete_one(query)
    return result.deleted_count > 0


def format_version_id(version: dict) -> dict:
    """
    Helper: Chuyển đổi ObjectId sang string phục vụ trả JSON API.
    """
    ver_copy = dict(version)

    if "_id" in ver_copy:
        ver_copy["id"] = str(ver_copy.pop("_id"))

    if "document_id" in ver_copy and ver_copy["document_id"] is not None:
        ver_copy["document_id"] = str(ver_copy["document_id"])

    if "created_by" in ver_copy and ver_copy["created_by"] is not None:
        ver_copy["created_by"] = str(ver_copy["created_by"])

    return ver_copy
