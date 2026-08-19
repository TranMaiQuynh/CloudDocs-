"""
routers/comments.py
===================
Mô tả:
    API Router quản lý các bình luận/ghi chú (Comments) trên tài liệu.
"""

from fastapi import APIRouter, Depends, status, HTTPException
from typing import List
from bson import ObjectId
from app.schemas.comment_schema import CommentCreateRequest, CommentResponse
from app.repositories import comment_repository
from app.services.permission_service import check_user_access, AccessLevel
from app.dependencies.auth_deps import get_current_user
from app.database.connection import database

users_collection = database["users"]

router = APIRouter(
    prefix="/documents",
    tags=["Comments"],
)


@router.post(
    "/{doc_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Gửi bình luận mới trên tài liệu",
    description="""
    Gửi một bình luận/ghi chú mới thảo luận về nội dung của tài liệu.
    
    **Phân quyền:**
    - Người dùng phải có quyền đọc (Viewer) trở lên đối với tài liệu đó.
    """,
)
async def create_comment(
    doc_id: str,
    request: CommentCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    # 1. Xác thực quyền đọc trên tài liệu
    has_read = await check_user_access(
        user_id=current_user["id"],
        resource_id=doc_id,
        resource_type="document",
        required_level=AccessLevel.VIEWER
    )
    if not has_read:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền bình luận trên tài liệu này."
        )

    # 2. Tìm tên hiển thị của user thực hiện bình luận
    user_doc = await users_collection.find_one({"_id": ObjectId(current_user["id"])}, {"full_name": 1})
    user_name = user_doc.get("full_name") if user_doc else "Collaborator"

    # 3. Tạo bình luận trong DB
    comment = await comment_repository.create_comment(
        document_id=doc_id,
        user_id=current_user["id"],
        user_name=user_name,
        content=request.content
    )

    return comment_repository.format_comment_id(comment)


@router.get(
    "/{doc_id}/comments",
    response_model=List[CommentResponse],
    status_code=status.HTTP_200_OK,
    summary="Xem danh sách bình luận trên tài liệu",
    description="""
    Lấy toàn bộ lịch sử các bình luận và thảo luận của tài liệu, sắp xếp từ cũ nhất đến mới nhất.
    
    **Phân quyền:**
    - Người dùng phải có quyền đọc (Viewer) trở lên đối với tài liệu đó.
    """,
)
async def list_comments(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    # 1. Xác thực quyền đọc trên tài liệu
    has_read = await check_user_access(
        user_id=current_user["id"],
        resource_id=doc_id,
        resource_type="document",
        required_level=AccessLevel.VIEWER
    )
    if not has_read:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xem bình luận của tài liệu này."
        )

    # 2. Lấy danh sách bình luận
    comments = await comment_repository.find_by_document(doc_id)
    return [comment_repository.format_comment_id(c) for c in comments]
