"""
routers/documents.py
====================
Mô tả:
    API Layer cho Document — định nghĩa các HTTP endpoints để tải lên, tải xuống, đổi tên, xóa, di chuyển và tìm kiếm tài liệu.
    Tích hợp các chốt chặn xác thực (JWT) và phân quyền đệ quy (ACL).
"""

from fastapi import APIRouter, Depends, status, Query, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from typing import List, Optional
from io import BytesIO
from urllib.parse import quote
from app.schemas.document_schema import DocumentRenameRequest, DocumentResponse, DocumentMoveRequest, DocumentUpdateRequest
from app.schemas.user_schema import MessageResponse
from app.services import document_service
from app.dependencies.auth_deps import get_current_user

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tải lên tài liệu mới",
    description="""
    Tải lên một tài liệu mới (file nhị phân) và lưu vào thư mục cụ thể (hoặc thư mục gốc).
    
    **Phân quyền:**
    - Admin/Leader có quyền tải lên gốc.
    - Member có quyền Editor trên thư mục đích cũng được phép tải lên.
    """,
)
async def upload_document(
    file: UploadFile = File(..., description="Tệp tin cần tải lên"),
    folder_id: Optional[str] = Form(None, description="ID thư mục lưu trữ tài liệu, để trống nếu ở gốc"),
    description: Optional[str] = Form("", description="Mô tả tóm tắt về tài liệu"),
    tags: Optional[str] = Form(None, description="Danh sách nhãn phân loại, cách nhau bằng dấu phẩy"),
    custom_name: Optional[str] = Form(None, description="Tên tệp tin tùy chỉnh"),
    current_user: dict = Depends(get_current_user)
):
    """
    Tải tài liệu mới lên.
    """
    if custom_name and custom_name.strip():
        import os
        _, ext = os.path.splitext(file.filename)
        _, custom_ext = os.path.splitext(custom_name)
        if not custom_ext and ext:
            file.filename = custom_name.strip() + ext
        else:
            file.filename = custom_name.strip()

    tags_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    result = await document_service.upload_document(
        file=file,
        folder_id=folder_id if folder_id else None,
        created_by=current_user["id"],
        description=description or "",
        tags=tags_list
    )
    return result


@router.post(
    "/{doc_id}/versions",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tải lên phiên bản mới của tài liệu",
    description="""
    Tải lên một phiên bản tài liệu mới thay thế phiên bản cũ. Số phiên bản tự động tăng lên.
    
    **Phân quyền:**
    - Người dùng có quyền Editor trên tài liệu.
    """,
)
async def upload_new_version(
    doc_id: str,
    file: UploadFile = File(..., description="Tệp tin phiên bản mới"),
    change_log: Optional[str] = Form("", description="Lịch sử các thay đổi của phiên bản này"),
    current_user: dict = Depends(get_current_user)
):
    """
    Tải lên phiên bản tài liệu mới.
    """
    result = await document_service.upload_new_version(
        doc_id=doc_id,
        file=file,
        created_by=current_user["id"],
        change_log=change_log or ""
    )
    return result


@router.get(
    "/quota",
    status_code=status.HTTP_200_OK,
    summary="Lấy hạn mức và dung lượng lưu trữ đã dùng",
    description="""
    Tính toán tổng dung lượng lưu trữ đã dùng của người dùng hiện tại (tính bằng bytes) trên tổng hạn mức 50MB.
    """,
)
async def get_storage_quota(
    current_user: dict = Depends(get_current_user)
):
    from app.database.connection import database
    from bson import ObjectId
    docs_col = database["documents"]
    user_oid = ObjectId(current_user["id"])
    cursor = docs_col.find({"created_by": user_oid, "is_deleted": False}, {"file_size": 1})
    total_used = 0
    async for d in cursor:
        total_used += d.get("file_size", 0)
        
    return {
        "limit_bytes": 52428800,
        "used_bytes": total_used
    }


@router.get(
    "/trash",
    response_model=List[DocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách tài liệu trong thùng rác",
    description="""
    Lấy danh sách các tài liệu đã bị xóa mềm của người dùng hiện tại.
    """,
)
async def list_trash_documents(
    current_user: dict = Depends(get_current_user)
):
    """
    Lấy danh sách tài liệu đã bị xóa mềm.
    """
    result = await document_service.list_trash_documents(user_id=current_user["id"])
    return result


@router.get(
    "/{doc_id}/download",
    summary="Tải xuống tài liệu trực tiếp",
    description="""
    Tải trực tiếp tài liệu về máy cá nhân từ Supabase Storage. Hỗ trợ chọn số phiên bản.
    
    **Phân quyền:**
    - Người dùng có quyền đọc (Viewer) trở lên.
    """,
)
async def download_document(
    doc_id: str,
    version_number: Optional[int] = Query(None, description="Số phiên bản cần tải, mặc định tải phiên bản mới nhất"),
    current_user: dict = Depends(get_current_user)
):
    """
    Tải xuống tài liệu dưới dạng Stream trực tiếp từ Supabase.
    """
    file_bytes, doc = await document_service.download_document(
        doc_id=doc_id,
        user_id=current_user["id"],
        version_number=version_number
    )
    
    # Encode tên file tiếng Việt/tránh lỗi Header
    encoded_filename = quote(doc["name"])
    
    return StreamingResponse(
        BytesIO(file_bytes),
        media_type=doc["mime_type"],
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.get(
    "/{doc_id}/presigned-url",
    summary="Lấy link tải tài liệu bảo mật",
    description="""
    Tạo link signed URL bảo mật có giới hạn thời gian (mặc định 1 giờ) để tải file.
    
    **Phân quyền:**
    - Người dùng có quyền đọc (Viewer) trở lên.
    """,
)
async def get_presigned_download_url(
    doc_id: str,
    version_number: Optional[int] = Query(None, description="Số phiên bản, mặc định là mới nhất"),
    expires_in: int = Query(3600, description="Thời gian sống của URL tính bằng giây (mặc định 3600s = 1 giờ)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Tạo link tải bảo mật.
    """
    url = await document_service.get_presigned_download_url(
        doc_id=doc_id,
        user_id=current_user["id"],
        version_number=version_number,
        expires_in=expires_in
    )
    return {"url": url}


@router.patch(
    "/{doc_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật chi tiết tài liệu",
    description="""
    Cập nhật tên, mô tả hoặc nhãn phân loại của tài liệu.
    
    **Phân quyền:**
    - Người dùng có quyền Editor trở lên.
    """,
)
async def update_document_details(
    doc_id: str,
    request: DocumentUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Cập nhật metadata tài liệu.
    """
    result = await document_service.update_document_details(
        doc_id=doc_id,
        request=request,
        user_id=current_user["id"]
    )
    return result


@router.patch(
    "/{doc_id}/rename",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Đổi tên tài liệu",
    description="""
    Thay đổi tên hiển thị của tài liệu dựa trên ID.
    
    **Phân quyền:**
    - Người dùng phải có quyền ghi (Editor) trở lên.
    """,
)
async def rename_document(
    doc_id: str,
    request: DocumentRenameRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Đổi tên hiển thị tài liệu.
    """
    result = await document_service.rename_document(
        doc_id=doc_id,
        request=request,
        user_id=current_user["id"]
    )
    return result


@router.patch(
    "/{doc_id}/move",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Di chuyển vị trí tài liệu",
    description="""
    Di chuyển tài liệu sang một thư mục đích khác.
    
    **Phân quyền:**
    - Người dùng phải có quyền ghi (Editor) trở lên.
    """,
)
async def move_document(
    doc_id: str,
    request: DocumentMoveRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Di chuyển vị trí tài liệu.
    """
    result = await document_service.move_document(
        doc_id=doc_id,
        target_folder_id=request.target_folder_id,
        user_id=current_user["id"]
    )
    return result


@router.delete(
    "/{doc_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Xóa mềm tài liệu (Chuyển vào thùng rác)",
    description="""
    Đưa tài liệu này vào thùng rác. File vật lý vẫn còn nguyên trên cloud storage để có thể khôi phục.
    
    **Phân quyền:**
    - Người dùng phải có quyền ghi (Editor) trở lên.
    """,
)
async def delete_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Xóa mềm tài liệu.
    """
    result = await document_service.delete_document(
        doc_id=doc_id,
        user_id=current_user["id"]
    )
    return result


@router.post(
    "/{doc_id}/restore",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Khôi phục tài liệu",
    description="""
    Khôi phục tài liệu đã xóa mềm khỏi thùng rác.
    
    **Phân quyền:**
    - Người dùng có quyền ghi (Editor) trở lên.
    """,
)
async def restore_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Khôi phục tài liệu.
    """
    result = await document_service.restore_document(
        doc_id=doc_id,
        user_id=current_user["id"]
    )
    return result


@router.delete(
    "/{doc_id}/hard",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Xóa cứng vĩnh viễn tài liệu",
    description="""
    Xóa vĩnh viễn tài liệu khỏi cơ sở dữ liệu MongoDB và xóa toàn bộ các tệp vật lý trên Supabase Storage. Không thể khôi phục.
    
    **Phân quyền:**
    - Người dùng có quyền ghi (Editor) trở lên.
    """,
)
async def hard_delete_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Xóa vĩnh viễn tài liệu.
    """
    result = await document_service.hard_delete_document(
        doc_id=doc_id,
        user_id=current_user["id"]
    )
    return result


@router.get(
    "/search",
    response_model=List[DocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="Tìm kiếm tài liệu",
    description="""
    Tìm kiếm tài liệu theo từ khóa tên và có thể lọc theo thư mục cụ thể.
    
    **Phân quyền:**
    - Người dùng có quyền đọc (Viewer) đối với các file kết quả.
    """,
)
async def search_documents(
    q: str = Query("", description="Từ khóa tìm kiếm trong tên file"),
    folder_id: Optional[str] = Query(None, description="Lọc theo ID thư mục cụ thể"),
    current_user: dict = Depends(get_current_user)
):
    """
    Tìm kiếm tài liệu.
    """
    result = await document_service.search_documents(
        query=q,
        user_id=current_user["id"],
        folder_id=folder_id
    )
    return result


@router.get(
    "/{doc_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy chi tiết tài liệu theo ID",
    description="""
    Lấy thông tin chi tiết metadata của một tài liệu dựa trên ID.
    
    **Phân quyền:**
    - Người dùng có quyền đọc (Viewer) đối với tài liệu này.
    """,
)
async def get_document_by_id(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Lấy chi tiết tài liệu theo ID.
    """
    result = await document_service.get_document_by_id(
        doc_id=doc_id,
        user_id=current_user["id"]
    )
    return result
