"""
services/document_service.py
============================
Mô tả:
    Business Logic Layer cho Document.
    Kết nối Supabase Storage (lưu trữ file nhị phân) và MongoDB (lưu metadata).
    Hỗ trợ Versioning và cơ chế Xóa mềm/Khôi phục/Xóa cứng tích hợp phân quyền ACL đệ quy.
"""

import re
import uuid
import unicodedata
from typing import List, Optional, Tuple
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import HTTPException, status, UploadFile
from app.storage.supabase import upload_file, download_file, delete_file, get_presigned_url
from app.repositories import document_repository, folder_repository, version_repository, activity_repository
from app.schemas.document_schema import DocumentRenameRequest, DocumentUpdateRequest
from app.services.permission_service import check_user_access, AccessLevel
from app.database.connection import database

users_collection = database["users"]


def sanitize_filename(filename: str) -> str:
    """Chuyển tên file vật lý sang chuẩn ASCII safe cho Cloud Storage mà vẫn giữ nguyên extension."""
    if not filename:
        return "file"
    if "." in filename:
        name_part, ext = filename.rsplit(".", 1)
        ext = f".{ext.lower()}"
    else:
        name_part, ext = filename, ""

    name_part = unicodedata.normalize('NFKD', name_part).encode('ASCII', 'ignore').decode('utf-8')
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name_part)
    safe_name = re.sub(r'_+', '_', safe_name).strip('_')
    return f"{safe_name or 'file'}{ext}"


async def upload_document(
    file: UploadFile,
    folder_id: Optional[str],
    created_by: str,
    description: str = "",
    tags: List[str] = []
) -> dict:
    """
    Tải tài liệu mới lên Supabase Storage và lưu thông tin chi tiết vào MongoDB.
    Đồng thời tự động tạo Phiên bản 1 (Version 1) lưu vào lịch sử.
    """
    # 1. Kiểm tra phân quyền tạo
    if folder_id:
        folder = await folder_repository.find_by_id(folder_id)
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thư mục chứa tài liệu không tồn tại hoặc đã bị xóa."
            )
        # Đệ quy check quyền ghi trên thư mục cha
        has_write = await check_user_access(created_by, folder_id, "folder", AccessLevel.EDITOR)
        if not has_write:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền tải tài liệu lên thư mục này."
            )
    else:
        # Cho phép bất kỳ người dùng nào tải tệp lên gốc (root)
        pass

    # 2. Đọc dữ liệu file nhị phân
    try:
        file_content = await file.read()
        file_size = len(file_content)
        mime_type = file.content_type or "application/octet-stream"
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể đọc tệp tin tải lên: {str(e)}"
        )

    # Kiểm tra giới hạn dung lượng lưu trữ 50MB (52,428,800 bytes)
    cursor = database["documents"].find({"created_by": ObjectId(created_by), "is_deleted": False}, {"file_size": 1})
    total_used = 0
    async for d in cursor:
        total_used += d.get("file_size", 0)

    if total_used + file_size > 52428800:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tải tệp tin thất bại. Tổng dung lượng lưu trữ của bạn sẽ vượt quá hạn mức 50MB."
        )

    # 3. Tạo đường dẫn lưu trữ độc nhất trên Cloud Storage
    folder_path = f"folders/{folder_id}" if folder_id else "root"
    safe_filename = sanitize_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}-{safe_filename}"
    storage_path = f"{folder_path}/{unique_filename}"

    # 4. Upload lên Supabase Storage qua helper
    try:
        upload_file(
            file_data=file_content,
            dest_path=storage_path,
            content_type=mime_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lưu trữ file vật lý lên Supabase: {str(e)}"
        )

    # 5. Lưu thông tin metadata tài liệu vào MongoDB
    new_doc = await document_repository.create_document(
        name=file.filename,
        folder_id=folder_id,
        storage_path=storage_path,
        file_size=file_size,
        mime_type=mime_type,
        created_by=created_by,
        current_version=1,
        description=description,
        tags=tags,
    )

    doc_id = str(new_doc["_id"])

    # 6. Tạo bản ghi phiên bản 1 trong lịch sử
    await version_repository.create_version(
        document_id=doc_id,
        version_number=1,
        storage_path=storage_path,
        file_size=file_size,
        created_by=created_by,
        change_log="Phiên bản khởi tạo ban đầu."
    )

    # Ghi nhận nhật ký hoạt động
    user_doc = await users_collection.find_one({"_id": ObjectId(created_by)}, {"full_name": 1})
    user_name = user_doc.get("full_name") if user_doc else "Học viên"
    await activity_repository.create_activity(
        user_id=created_by,
        user_name=user_name,
        action="UPLOAD",
        resource_name=file.filename,
        details=f"Đã tải lên tệp tin mới '{file.filename}'."
    )

    return document_repository.format_document_id(new_doc)


async def upload_new_version(
    doc_id: str,
    file: UploadFile,
    created_by: str,
    change_log: str = ""
) -> dict:
    """
    Tải lên một phiên bản mới cho tài liệu đã tồn tại.
    Tự động tăng số phiên bản (Version Number) và lưu trữ lịch sử.
    """
    # 1. Kiểm tra tài liệu gốc có tồn tại không
    doc = await document_repository.find_by_id(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tài liệu cần cập nhật phiên bản không tồn tại."
        )

    # Kiểm tra quyền ghi (Editor) trên tài liệu
    has_write = await check_user_access(created_by, doc_id, "document", AccessLevel.EDITOR)
    if not has_write:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền sửa đổi hoặc tải phiên bản mới cho tài liệu này."
        )

    # 2. Đọc file
    try:
        file_content = await file.read()
        file_size = len(file_content)
        mime_type = file.content_type or "application/octet-stream"
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể đọc file cập nhật: {str(e)}"
        )

    # Kiểm tra giới hạn dung lượng lưu trữ 50MB (trừ đi dung lượng của file cũ trước khi thay thế)
    cursor = database["documents"].find({"created_by": ObjectId(created_by), "is_deleted": False}, {"file_size": 1})
    total_used = 0
    async for d in cursor:
        total_used += d.get("file_size", 0)

    old_size = doc.get("file_size", 0)
    if total_used - old_size + file_size > 52428800:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tải phiên bản mới thất bại. Tổng dung lượng lưu trữ của bạn sẽ vượt quá hạn mức 50MB."
        )

    # 3. Tạo version mới
    new_version_number = doc.get("current_version", 1) + 1
    folder_id = str(doc["folder_id"]) if doc.get("folder_id") else "root"
    safe_filename = sanitize_filename(file.filename)
    storage_path = f"folders/{folder_id}/{uuid.uuid4()}-{safe_filename}"

    # 4. Upload file lên Supabase
    try:
        upload_file(
            file_data=file_content,
            dest_path=storage_path,
            content_type=mime_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Không thể tải phiên bản mới lên Cloud Storage: {str(e)}"
        )

    # 5. Lưu phiên bản mới vào lịch sử phiên bản
    await version_repository.create_version(
        document_id=doc_id,
        version_number=new_version_number,
        storage_path=storage_path,
        file_size=file_size,
        created_by=created_by,
        change_log=change_log or f"Cập nhật lên phiên bản {new_version_number}."
    )

    # 6. Cập nhật metadata chính trong Document
    update_payload = {
        "current_version": new_version_number,
        "storage_path": storage_path,
        "file_size": file_size,
        "mime_type": mime_type,
        "name": file.filename
    }
    updated_doc = await document_repository.update_document(doc_id, update_payload)

    # Ghi nhận nhật ký hoạt động
    user_doc = await users_collection.find_one({"_id": ObjectId(created_by)}, {"full_name": 1})
    user_name = user_doc.get("full_name") if user_doc else "Học viên"
    await activity_repository.create_activity(
        user_id=created_by,
        user_name=user_name,
        action="NEW_VERSION",
        resource_name=file.filename,
        details=f"Đã cập nhật phiên bản mới v{new_version_number} cho tệp tin '{file.filename}'."
    )

    return document_repository.format_document_id(updated_doc)


async def download_document(
    doc_id: str,
    user_id: str,
    version_number: Optional[int] = None
) -> Tuple[bytes, dict]:
    """
    Tải file từ Supabase Storage và trả về bytes nội dung cùng thông tin tài liệu.
    """
    # Kiểm tra quyền đọc (Viewer) trên tài liệu
    has_read = await check_user_access(user_id, doc_id, "document", AccessLevel.VIEWER)
    if not has_read:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền tải xuống tài liệu này."
        )

    # 1. Tìm thông tin metadata tài liệu
    doc = await document_repository.find_by_id(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tài liệu không tồn tại hoặc đã bị xóa."
        )

    target_path = doc["storage_path"]

    # 2. Nếu tải phiên bản cụ thể
    if version_number is not None:
        version = await version_repository.find_by_document_and_number(doc_id, version_number)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Phiên bản thứ {version_number} của tài liệu này không tồn tại."
            )
        target_path = version["storage_path"]

    # 3. Tải xuống file nhị phân từ Supabase Storage
    try:
        file_bytes = download_file(target_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Không thể tải tệp tin từ Cloud Storage: {str(e)}"
        )

    return file_bytes, doc


async def get_presigned_download_url(
    doc_id: str,
    user_id: str,
    version_number: Optional[int] = None,
    expires_in: int = 3600
) -> str:
    """
    Tạo link tải file bảo mật tạm thời (Presigned URL) có giới hạn thời gian.
    """
    has_read = await check_user_access(user_id, doc_id, "document", AccessLevel.VIEWER)
    if not has_read:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập liên kết tải bảo mật cho tài liệu này."
        )

    doc = await document_repository.find_by_id(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tài liệu không tồn tại hoặc đã bị xóa."
        )

    target_path = doc["storage_path"]

    if version_number is not None:
        version = await version_repository.find_by_document_and_number(doc_id, version_number)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Phiên bản {version_number} không tồn tại."
            )
        target_path = version["storage_path"]

    try:
        url = get_presigned_url(target_path, expires_in)
        return url
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Không thể tạo liên kết tải bảo mật: {str(e)}"
        )


async def rename_document(doc_id: str, request: DocumentRenameRequest, user_id: str) -> dict:
    """
    Đổi tên hiển thị của tài liệu.
    """
    has_write = await check_user_access(user_id, doc_id, "document", AccessLevel.EDITOR)
    if not has_write:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền chỉnh sửa tài liệu này."
        )

    doc = await document_repository.find_by_id(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tài liệu không tồn tại hoặc đã bị xóa."
        )

    updated_doc = await document_repository.rename_document(doc_id, request.name)
    
    # Ghi nhận nhật ký hoạt động
    user_doc = await users_collection.find_one({"_id": ObjectId(user_id)}, {"full_name": 1})
    user_name = user_doc.get("full_name") if user_doc else "Học viên"
    await activity_repository.create_activity(
        user_id=user_id,
        user_name=user_name,
        action="RENAME",
        resource_name=request.name,
        details=f"Đã đổi tên tệp tin '{doc['name']}' thành '{request.name}'."
    )
    return document_repository.format_document_id(updated_doc)


async def update_document_details(doc_id: str, request: DocumentUpdateRequest, user_id: str) -> dict:
    """
    Cập nhật thông tin chi tiết (tên, mô tả, thẻ) của tài liệu.
    """
    has_write = await check_user_access(user_id, doc_id, "document", AccessLevel.EDITOR)
    if not has_write:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền chỉnh sửa thông tin tài liệu này."
        )

    doc = await document_repository.find_by_id(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tài liệu không tồn tại hoặc đã bị xóa."
        )

    update_data = {}
    if request.name is not None:
        update_data["name"] = request.name
    if request.description is not None:
        update_data["description"] = request.description
    if request.tags is not None:
        update_data["tags"] = request.tags

    if not update_data:
        return document_repository.format_document_id(doc)

    updated_doc = await document_repository.update_document(doc_id, update_data)
    
    # Ghi nhận nhật ký hoạt động
    user_doc = await users_collection.find_one({"_id": ObjectId(user_id)}, {"full_name": 1})
    user_name = user_doc.get("full_name") if user_doc else "Học viên"
    await activity_repository.create_activity(
        user_id=user_id,
        user_name=user_name,
        action="UPDATE_METADATA",
        resource_name=doc["name"],
        details=f"Đã cập nhật thông tin tài liệu '{doc['name']}'."
    )
    return document_repository.format_document_id(updated_doc)


async def move_document(doc_id: str, target_folder_id: Optional[str], user_id: str) -> dict:
    """
    Di chuyển tài liệu sang một thư mục khác.
    """
    # 1. Kiểm tra quyền trên document (yêu cầu Editor)
    has_write = await check_user_access(user_id, doc_id, "document", AccessLevel.EDITOR)
    if not has_write:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền di chuyển tài liệu này."
        )

    doc = await document_repository.find_by_id(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tài liệu không tồn tại."
        )

    # 2. Kiểm tra quyền trên thư mục đích
    if target_folder_id:
        folder = await folder_repository.find_by_id(target_folder_id)
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thư mục đích không tồn tại hoặc đã bị xóa."
            )
        
        target_has_write = await check_user_access(user_id, target_folder_id, "folder", AccessLevel.EDITOR)
        if not target_has_write:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền ghi dữ liệu lên thư mục đích này."
            )
    else:
        # Cho phép bất kỳ người dùng nào di chuyển tệp ra gốc (root)
        pass

    updated_doc = await document_repository.update_document(doc_id, {"folder_id": target_folder_id})
    
    # Ghi nhận nhật ký hoạt động
    user_doc = await users_collection.find_one({"_id": ObjectId(user_id)}, {"full_name": 1})
    user_name = user_doc.get("full_name") if user_doc else "Học viên"
    dest = f"thư mục ID {target_folder_id}" if target_folder_id else "thư mục gốc"
    await activity_repository.create_activity(
        user_id=user_id,
        user_name=user_name,
        action="MOVE",
        resource_name=doc["name"],
        details=f"Đã di chuyển tệp tin '{doc['name']}' sang {dest}."
    )
    return document_repository.format_document_id(updated_doc)


async def delete_document(doc_id: str, user_id: str) -> dict:
    """
    Xóa mềm (Soft Delete) tài liệu, chuyển vào thùng rác.
    """
    has_write = await check_user_access(user_id, doc_id, "document", AccessLevel.EDITOR)
    if not has_write:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xóa tài liệu này."
        )

    doc = await document_repository.find_by_id(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tài liệu không tồn tại hoặc đã bị xóa."
        )

    success = await document_repository.soft_delete_document(doc_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể thực hiện xóa mềm tài liệu này."
        )

    # Ghi nhận nhật ký hoạt động
    user_doc = await users_collection.find_one({"_id": ObjectId(user_id)}, {"full_name": 1})
    user_name = user_doc.get("full_name") if user_doc else "Học viên"
    await activity_repository.create_activity(
        user_id=user_id,
        user_name=user_name,
        action="DELETE",
        resource_name=doc["name"],
        details=f"Đã di chuyển tệp tin '{doc['name']}' vào thùng rác."
    )

    return {
        "success": True,
        "message": f"Đã đưa tài liệu '{doc['name']}' vào thùng rác."
    }


async def restore_document(doc_id: str, user_id: str) -> dict:
    """
    Khôi phục tài liệu đã bị xóa mềm khỏi thùng rác.
    """
    has_write = await check_user_access(user_id, doc_id, "document", AccessLevel.EDITOR)
    if not has_write:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền khôi phục tài liệu này."
        )

    doc = await document_repository.find_by_id(doc_id, include_deleted=True)
    if not doc or not doc.get("is_deleted"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tài liệu không tồn tại trong thùng rác."
        )

    # Nếu thư mục chứa tài liệu này cũng bị xóa mềm, không cho phép khôi phục lẻ tài liệu
    if doc.get("folder_id"):
        parent_folder = await folder_repository.find_by_id(str(doc["folder_id"]), include_deleted=True)
        if parent_folder and parent_folder.get("is_deleted"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thư mục chứa tài liệu này vẫn đang nằm trong thùng rác. Vui lòng khôi phục thư mục cha trước."
            )

    success = await document_repository.restore_document(doc_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể khôi phục tài liệu."
        )

    # Ghi nhận nhật ký hoạt động
    user_doc = await users_collection.find_one({"_id": ObjectId(user_id)}, {"full_name": 1})
    user_name = user_doc.get("full_name") if user_doc else "Học viên"
    await activity_repository.create_activity(
        user_id=user_id,
        user_name=user_name,
        action="RESTORE",
        resource_name=doc["name"],
        details=f"Đã khôi phục tệp tin '{doc['name']}' từ thùng rác."
    )

    return {
        "success": True,
        "message": f"Đã khôi phục tài liệu '{doc['name']}' thành công."
    }


async def hard_delete_document(doc_id: str, user_id: str) -> dict:
    """
    Xóa cứng vĩnh viễn tài liệu khỏi MongoDB và xóa toàn bộ file vật lý/phiên bản lịch sử trên Supabase Storage.
    """
    has_write = await check_user_access(user_id, doc_id, "document", AccessLevel.EDITOR)
    if not has_write:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xóa vĩnh viễn tài liệu này."
        )

    doc = await document_repository.find_by_id(doc_id, include_deleted=True)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tài liệu không tồn tại."
        )

    # 1. Tìm tất cả phiên bản để lấy đường dẫn file vật lý
    versions = await version_repository.find_by_document(doc_id)
    paths_to_delete = [doc["storage_path"]]
    for v in versions:
        if v["storage_path"] not in paths_to_delete:
            paths_to_delete.append(v["storage_path"])

    # 2. Xóa các tệp nhị phân trên Supabase Storage
    for path in paths_to_delete:
        try:
            delete_file(path)
        except Exception as e:
            print(f"Cảnh báo: Lỗi xóa file vật lý '{path}' trên Supabase: {str(e)}")

    # 3. Xóa lịch sử phiên bản trong MongoDB
    await version_repository.delete_all_by_document(doc_id)

    # 4. Xóa tài liệu gốc khỏi MongoDB
    await document_repository.hard_delete_document(doc_id)

    # Ghi nhận nhật ký hoạt động
    user_doc = await users_collection.find_one({"_id": ObjectId(user_id)}, {"full_name": 1})
    user_name = user_doc.get("full_name") if user_doc else "Học viên"
    await activity_repository.create_activity(
        user_id=user_id,
        user_name=user_name,
        action="HARD_DELETE",
        resource_name=doc["name"],
        details=f"Đã xóa vĩnh viễn tệp tin '{doc['name']}' khỏi hệ thống."
    )

    return {
        "success": True,
        "message": f"Đã xóa vĩnh viễn tài liệu '{doc['name']}' và toàn bộ lịch sử phiên bản thành công."
    }


async def search_documents(query: str, user_id: str, folder_id: Optional[str] = None) -> List[dict]:
    """
    Tìm kiếm tài liệu và lọc ra những tài liệu mà user có quyền đọc (Viewer).
    """
    if folder_id:
        folder = await folder_repository.find_by_id(folder_id)
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thư mục lọc không tồn tại."
            )
        # Check quyền đọc trên thư mục lọc
        has_read = await check_user_access(user_id, folder_id, "folder", AccessLevel.VIEWER)
        if not has_read:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền truy cập thư mục này."
            )

    docs = await document_repository.search_documents(query=query, folder_id=folder_id)
    
    # Lọc danh sách theo ACL của user
    user_docs = []
    for d in docs:
        # Nếu đang lấy danh sách gốc (query rỗng, folder_id rỗng) và file đã chia sẻ cho group, loại bỏ khỏi Trang chủ
        if not folder_id and not query:
            is_group_shared = await database["permissions"].find_one({
                "resource_id": d["_id"],
                "resource_type": "document",
                "share_type": "group"
            })
            if is_group_shared:
                continue

        d_id = str(d["_id"])
        has_access = await check_user_access(user_id, d_id, "document", AccessLevel.VIEWER, allow_link_sharing=False)
        if has_access:
            user_docs.append(d)
            
    return [document_repository.format_document_id(d) for d in user_docs]


async def list_trash_documents(user_id: str) -> List[dict]:
    """
    Lấy danh sách tài liệu đã bị xóa mềm của người dùng.
    """
    docs = await document_repository.find_deleted_documents(user_id)
    return [document_repository.format_document_id(d) for d in docs]


async def get_document_by_id(doc_id: str, user_id: str) -> dict:
    """
    Lấy thông tin chi tiết một tài liệu theo ID và kiểm tra quyền truy cập.
    """
    has_read = await check_user_access(user_id, doc_id, "document", AccessLevel.VIEWER)
    if not has_read:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập tài liệu này."
        )

    doc = await document_repository.find_by_id(doc_id)
    if not doc or doc.get("is_deleted", False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tài liệu không tồn tại hoặc đã bị xóa."
        )

    return document_repository.format_document_id(doc)
