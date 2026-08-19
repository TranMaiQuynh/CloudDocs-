"""
services/version_service.py
===========================
Mô tả:
    Business Logic Layer cho quản lý Lịch sử Phiên bản (Versioning) và Quay ngược thời gian (Rollback).
"""

from typing import List
from fastapi import HTTPException, status
from app.repositories import version_repository, document_repository
from app.services.permission_service import check_user_access, AccessLevel


async def list_document_versions(doc_id: str, user_id: str) -> List[dict]:
    """
    Lấy toàn bộ lịch sử phiên bản của một tài liệu.
    Yêu cầu quyền xem (Viewer) tài liệu.
    """
    # Kiểm tra quyền truy cập tài liệu
    has_read = await check_user_access(user_id, doc_id, "document", AccessLevel.VIEWER)
    if not has_read:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xem lịch sử phiên bản của tài liệu này."
        )

    # Tìm tài liệu gốc
    doc = await document_repository.find_by_id(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tài liệu không tồn tại."
        )

    versions = await version_repository.find_by_document(doc_id)
    return [version_repository.format_version_id(v) for v in versions]


async def rollback_to_version(doc_id: str, version_number: int, user_id: str) -> dict:
    """
    Quay ngược tài liệu về một phiên bản lịch sử cụ thể.
    Tuân thủ Immutable History: Tạo một phiên bản mới tiếp theo trỏ tới nội dung của phiên bản cũ.
    Yêu cầu quyền ghi (Editor) tài liệu.
    """
    # 1. Kiểm tra quyền ghi
    has_write = await check_user_access(user_id, doc_id, "document", AccessLevel.EDITOR)
    if not has_write:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền chỉnh sửa (Rollback) tài liệu này."
        )

    # 2. Tìm tài liệu gốc
    doc = await document_repository.find_by_id(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tài liệu không tồn tại."
        )

    if doc.get("current_version", 1) == version_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài liệu hiện tại đã ở phiên bản này rồi."
        )

    # 3. Tìm bản ghi phiên bản lịch sử đích cần rollback về
    target_version = await version_repository.find_by_document_and_number(doc_id, version_number)
    if not target_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phiên bản lịch sử thứ {version_number} không tồn tại để khôi phục."
        )

    # 4. Xác định số phiên bản mới tiếp theo
    new_version_number = doc.get("current_version", 1) + 1

    # 5. Tạo bản ghi version mới trong lịch sử trỏ tới file vật lý của version cũ
    await version_repository.create_version(
        document_id=doc_id,
        version_number=new_version_number,
        storage_path=target_version["storage_path"],
        file_size=target_version["file_size"],
        created_by=user_id,
        change_log=f"Khôi phục tài liệu (Rollback) ngược về phiên bản {version_number}."
    )

    # 6. Cập nhật metadata chính của Document
    update_payload = {
        "current_version": new_version_number,
        "storage_path": target_version["storage_path"],
        "file_size": target_version["file_size"]
    }
    updated_doc = await document_repository.update_document(doc_id, update_payload)

    return document_repository.format_document_id(updated_doc)
