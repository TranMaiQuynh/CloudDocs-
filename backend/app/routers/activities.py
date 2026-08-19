"""
routers/activities.py
=====================
Mô tả:
    API Router quản lý Nhật ký hoạt động (Audit Trail).
"""

from fastapi import APIRouter, Depends, status
from typing import List
from bson import ObjectId
from app.schemas.activity_schema import ActivityResponse
from app.repositories import activity_repository
from app.dependencies.auth_deps import get_current_user
from app.database.connection import database

users_collection = database["users"]

router = APIRouter(
    prefix="/activities",
    tags=["Activities"],
)


@router.get(
    "",
    response_model=List[ActivityResponse],
    status_code=status.HTTP_200_OK,
    summary="Xem nhật ký hoạt động",
    description="""
    Xem lịch sử các hoạt động (Audit log) của hệ thống.
    - Với tài khoản có vai trò 'admin': Trả về nhật ký hoạt động của toàn bộ hệ thống.
    - Với tài khoản thông thường: Chỉ hiển thị nhật ký hoạt động của cá nhân người dùng đó.
    """,
)
async def list_activities(
    current_user: dict = Depends(get_current_user)
):
    # 1. Tìm thông tin chi tiết người dùng
    user = await users_collection.find_one({"_id": ObjectId(current_user["id"])}, {"role": 1})
    role = user.get("role") if user else "member"

    # 2. Phân nhánh lấy nhật ký dựa trên vai trò
    if role == "admin":
        activities = await activity_repository.find_all_activities(limit=100)
    else:
        activities = await activity_repository.find_by_user(user_id=current_user["id"], limit=50)

    return [activity_repository.format_activity_id(a) for a in activities]
