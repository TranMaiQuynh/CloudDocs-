"""
routers/notifications.py
========================
Mô tả:
    API Router quản lý các thông báo cá nhân (Notifications).
"""

from fastapi import APIRouter, Depends, status, HTTPException
from typing import List
from app.schemas.notification_schema import NotificationResponse
from app.repositories import notification_repository
from app.dependencies.auth_deps import get_current_user

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get(
    "",
    response_model=List[NotificationResponse],
    status_code=status.HTTP_200_OK,
    summary="Xem toàn bộ danh sách thông báo",
)
async def list_notifications(
    current_user: dict = Depends(get_current_user)
):
    notifs = await notification_repository.find_by_user(current_user["id"])
    return [notification_repository.format_notification_id(n) for n in notifs]


@router.post(
    "/{notif_id}/read",
    status_code=status.HTTP_200_OK,
    summary="Đánh dấu một thông báo là đã đọc",
)
async def mark_notification_read(
    notif_id: str,
    current_user: dict = Depends(get_current_user)
):
    success = await notification_repository.mark_as_read(notif_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thông báo không tồn tại hoặc lỗi xử lý."
        )
    return {"success": True}


@router.post(
    "/read-all",
    status_code=status.HTTP_200_OK,
    summary="Đánh dấu toàn bộ thông báo là đã đọc",
)
async def mark_all_notifications_read(
    current_user: dict = Depends(get_current_user)
):
    await notification_repository.mark_all_as_read(current_user["id"])
    return {"success": True}
