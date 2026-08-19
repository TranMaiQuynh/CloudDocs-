"""
routers/folders.py
==================
Mô tả:
    API Layer cho Folder — định nghĩa các HTTP endpoints để quản trị thư mục.
    Tích hợp các chốt chặn xác thực (JWT) và phân quyền kế thừa đệ quy (ACL).
"""

from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional
from app.schemas.folder_schema import (
    FolderCreateRequest,
    FolderUpdateRequest,
    FolderResponse
)
from app.schemas.user_schema import MessageResponse
from app.services import folder_service
from app.dependencies.auth_deps import get_current_user

# APIRouter cấu hình prefix và nhóm tags cho tài liệu Swagger/OpenAPI
router = APIRouter(
    prefix="/folders",
    tags=["Folders"],
)


@router.post(
    "",
    response_model=FolderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo thư mục mới",
    description="""
    Tạo một thư mục mới trong hệ thống.
    
    **Phân quyền:**
    - Admin/Leader có quyền tạo thư mục gốc.
    - Cả Member cũng được phép tạo thư mục con bên trong thư mục cha nếu có quyền Editor trên thư mục cha đó.
    """,
)
async def create_folder(
    request: FolderCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Tạo thư mục mới.
    """
    result = await folder_service.create_folder(
        request=request,
        created_by=current_user["id"]
    )
    return result


@router.get(
    "",
    response_model=List[FolderResponse],
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách thư mục con trực thuộc",
    description="""
    Lấy danh sách các thư mục con đang hoạt động trực thuộc một thư mục cha (hoặc thư mục gốc).
    
    **Phân quyền:**
    - Người dùng phải có quyền truy cập đọc (Viewer) trên thư mục cha.
    """,
)
async def list_folders(
    parent_id: Optional[str] = Query(
        default=None,
        description="ID của thư mục cha. Để trống/null nếu muốn lấy danh sách ở thư mục gốc."
    ),
    current_user: dict = Depends(get_current_user)
):
    """
    Lấy danh sách thư mục con.
    """
    result = await folder_service.list_folders(
        parent_id=parent_id,
        user_id=current_user["id"]
    )
    return result


@router.get(
    "/trash",
    response_model=List[FolderResponse],
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách thư mục trong thùng rác",
    description="""
    Lấy danh sách các thư mục đã bị xóa mềm của người dùng hiện tại.
    """,
)
async def list_trash_folders(
    current_user: dict = Depends(get_current_user)
):
    """
    Lấy danh sách thư mục đã bị xóa mềm.
    """
    result = await folder_service.list_trash_folders(user_id=current_user["id"])
    return result


@router.get(
    "/{folder_id}",
    response_model=FolderResponse,
    status_code=status.HTTP_200_OK,
    summary="Xem chi tiết thư mục",
    description="""
    Lấy thông tin chi tiết của một thư mục cụ thể dựa trên ID.
    
    **Phân quyền:**
    - Người dùng có quyền đọc (Viewer) trở lên.
    """,
)
async def get_folder(
    folder_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Xem chi tiết một thư mục.
    """
    result = await folder_service.get_folder_by_id(
        folder_id=folder_id,
        user_id=current_user["id"]
    )
    return result


@router.patch(
    "/{folder_id}",
    response_model=FolderResponse,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật thư mục (Đổi tên / sửa mô tả / di chuyển)",
    description="""
    Thay đổi tên, mô tả hoặc di chuyển thư mục dựa trên ID.
    
    **Phân quyền:**
    - Người dùng phải có quyền ghi (Editor) trở lên.
    """,
)
async def update_folder(
    folder_id: str,
    request: FolderUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Cập nhật thư mục.
    """
    result = await folder_service.rename_folder(
        folder_id=folder_id,
        request=request,
        user_id=current_user["id"]
    )
    return result


@router.delete(
    "/{folder_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Xóa mềm thư mục (Đưa vào thùng rác)",
    description="""
    Di chuyển một thư mục và đệ quy toàn bộ nội dung con của nó vào thùng rác.
    
    **Phân quyền:**
    - Người dùng phải có quyền ghi (Editor) trở lên.
    """,
)
async def delete_folder(
    folder_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Xóa mềm thư mục.
    """
    result = await folder_service.delete_folder(
        folder_id=folder_id,
        user_id=current_user["id"]
    )
    return result


@router.post(
    "/{folder_id}/restore",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Khôi phục thư mục đã xóa",
    description="""
    Khôi phục thư mục đã xóa mềm khỏi thùng rác và toàn bộ con đệ quy của nó.
    
    **Phân quyền:**
    - Người dùng phải có quyền ghi (Editor) trở lên.
    """,
)
async def restore_folder(
    folder_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Khôi phục thư mục.
    """
    result = await folder_service.restore_folder(
        folder_id=folder_id,
        user_id=current_user["id"]
    )
    return result
