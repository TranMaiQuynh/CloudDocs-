"""
routers/permissions.py
======================
Mô tả:
    API Router quản lý chia sẻ quyền (Permissions) trên tài liệu và thư mục.
"""

from fastapi import APIRouter, Depends, status, Query
from typing import List
from app.schemas.permission_schema import PermissionCreateRequest, PermissionResponse, LinkSharingResponse, LinkSharingUpdateRequest
from app.schemas.user_schema import MessageResponse
from app.services import permission_service
from app.dependencies.auth_deps import get_current_user

router = APIRouter(
    prefix="/permissions",
    tags=["Permissions"],
)


@router.post(
    "",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Chia sẻ tài nguyên (Thư mục / Tài liệu)",
    description="""
    Chia sẻ quyền truy cập đọc (viewer) hoặc sửa (editor) cho một người dùng khác thông qua email.
    
    **Phân quyền:**
    - Người chia sẻ phải có quyền Editor trở lên hoặc là Owner (người tạo) của tài nguyên đó.
    """,
)
async def share_resource(
    request: PermissionCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Chia sẻ tài nguyên cho tài khoản qua Email.
    """
    result = await permission_service.share_resource(
        request=request,
        granted_by=current_user["id"]
    )
    return result


@router.get(
    "/{resource_type}/{resource_id}",
    response_model=List[PermissionResponse],
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách cộng tác viên",
    description="""
    Lấy danh sách các tài khoản đang có quyền cộng tác trực tiếp trên tài liệu hoặc thư mục này.
    
    **Phân quyền:**
    - Người dùng phải có quyền Viewer (đọc) trở lên đối với tài nguyên đó.
    """,
)
async def get_resource_collaborators(
    resource_type: str,
    resource_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Lấy danh sách cộng tác viên của tài nguyên.
    """
    result = await permission_service.get_resource_collaborators(
        resource_id=resource_id,
        resource_type=resource_type,
        user_id=current_user["id"]
    )
    return result


@router.delete(
    "/{permission_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Thu hồi quyền truy cập",
    description="""
    Thu hồi (xóa) phân quyền chia sẻ của một cộng tác viên.
    
    **Phân quyền:**
    - Chỉ Admin, Owner của tài nguyên hoặc chính cộng tác viên đó tự rời khỏi nhóm chia sẻ mới được thực hiện.
    """,
)
async def revoke_permission(
    permission_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Thu hồi chia sẻ quyền.
    """
    result = await permission_service.revoke_permission(
        permission_id=permission_id,
        user_id=current_user["id"]
    )
    return result


@router.get(
    "/link-sharing/{resource_type}/{resource_id}",
    response_model=LinkSharingResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy cấu hình chia sẻ qua link",
)
async def get_link_sharing(
    resource_type: str,
    resource_id: str,
    current_user: dict = Depends(get_current_user)
):
    return await permission_service.get_link_sharing(
        resource_id=resource_id,
        resource_type=resource_type,
        user_id=current_user["id"]
    )


@router.post(
    "/link-sharing/{resource_type}/{resource_id}",
    response_model=LinkSharingResponse,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật cấu hình chia sẻ qua link",
)
async def update_link_sharing(
    resource_type: str,
    resource_id: str,
    request: LinkSharingUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    return await permission_service.update_link_sharing(
        resource_id=resource_id,
        resource_type=resource_type,
        share_link_access=request.share_link_access,
        share_link_level=request.share_link_level,
        user_id=current_user["id"]
    )
