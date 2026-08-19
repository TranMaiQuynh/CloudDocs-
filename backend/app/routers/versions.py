"""
routers/versions.py
===================
Mô tả:
    API Router quản lý lịch sử phiên bản (Versioning) và quay ngược thời gian (Rollback).
"""

from fastapi import APIRouter, Depends, status
from typing import List
from app.schemas.version_schema import VersionResponse
from app.schemas.document_schema import DocumentResponse
from app.services import version_service
from app.dependencies.auth_deps import get_current_user

router = APIRouter(
    prefix="/versions",
    tags=["Versions"],
)


@router.get(
    "/{doc_id}",
    response_model=List[VersionResponse],
    status_code=status.HTTP_200_OK,
    summary="Xem lịch sử phiên bản tài liệu",
    description="""
    Lấy danh sách tất cả các phiên bản đã lưu trong lịch sử của tài liệu.
    
    **Phân quyền:**
    - Người dùng phải có quyền truy cập đọc (Viewer) trở lên đối với tài liệu này.
    """,
)
async def list_versions(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Lấy danh sách lịch sử phiên bản.
    """
    result = await version_service.list_document_versions(
        doc_id=doc_id,
        user_id=current_user["id"]
    )
    return result


@router.post(
    "/{doc_id}/rollback/{version_number}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Quay ngược về phiên bản cũ",
    description="""
    Khôi phục tài liệu về phiên bản cũ hơn.
    Tạo một phiên bản mới tiếp theo có nội dung giống phiên bản chỉ định.
    
    **Phân quyền:**
    - Chỉ người dùng có quyền sửa (Editor) trở lên mới được phép thực hiện rollback.
    """,
)
async def rollback_version(
    doc_id: str,
    version_number: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Khôi phục phiên bản lịch sử.
    """
    result = await version_service.rollback_to_version(
        doc_id=doc_id,
        version_number=version_number,
        user_id=current_user["id"]
    )
    return result
