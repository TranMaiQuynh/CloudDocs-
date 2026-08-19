"""
models/user.py
==============
Mô tả:
    Đây là Data Model đại diện cho một User document trong MongoDB.
    Model này định nghĩa cấu trúc dữ liệu của 1 user, không chứa business logic.

Giao tiếp với:
    - repositories/user_repository.py : dùng model này để CRUD user trong DB
    - schemas/user_schema.py          : schema dùng model để build response

Design Pattern:
    Data Model / Entity — chỉ mô tả "user trông như thế nào", không làm gì thêm.

Lý do dùng TypedDict thay vì class thông thường:
    MongoDB trả về dict, TypedDict cho phép type hint mà không cần convert.
    Đơn giản, nhẹ, phù hợp cho dự án university.
"""

from typing import Optional
from datetime import datetime, timezone
from enum import Enum


class UserRole(str, Enum):
    """
    Enum định nghĩa các role trong hệ thống RBAC.

    Tại sao dùng Enum thay vì string thường?
    - Tránh typo (ví dụ: "Admin" vs "admin" vs "ADMIN")
    - IDE có thể autocomplete
    - Dễ refactor sau này
    - Khi thêm role mới, chỉ cần thêm vào đây

    Thứ tự quyền: ADMIN > LEADER > MEMBER
    """
    ADMIN = "admin"       # Quản trị viên hệ thống — toàn quyền
    LEADER = "leader"     # Trưởng nhóm — quản lý tài liệu nhóm
    MEMBER = "member"     # Thành viên — xem và download

# Hàm này để đảm bảo dữ liệu đã được chuẩn hóa
def create_user_document(
    email: str,
    hashed_password: str,
    full_name: str,
    role: UserRole = UserRole.MEMBER,
) -> dict:
    """
    Factory function tạo một user document mới để lưu vào MongoDB.

    Tại sao dùng function thay vì class với constructor?
    - MongoDB làm việc với dict, không cần ORM phức tạp
    - Dễ hiểu, không có magic nào ẩn bên trong
    - Phù hợp với Motor (async MongoDB driver)

    Args:
        email:           Email duy nhất của user (dùng làm username)
        hashed_password: Password đã được hash bằng bcrypt (KHÔNG PHẢI plaintext)
        full_name:       Tên đầy đủ của user
        role:            Vai trò trong hệ thống (mặc định: member)

    Returns:
        dict: Document sẵn sàng để insert vào MongoDB collection "users"

    Lưu ý về _id:
        Không set _id ở đây — MongoDB Atlas tự động tạo ObjectId duy nhất.
        Đây là best practice: để DB tự quản lý primary key.
    """
    now = datetime.now(timezone.utc)  # Luôn dùng UTC để tránh timezone bug

    return {
        # --- Identity ---
        "email": email.lower().strip(),  # normalize: tránh "User@Email.COM" ≠ "user@email.com"
        "full_name": full_name.strip(),

        # --- Security ---
        "hashed_password": hashed_password,  # bcrypt hash, KHÔNG BAO GIỜ lưu plaintext

        # --- RBAC ---
        "role": role.value,   # Lưu string ("admin"/"leader"/"member"), không lưu enum object

        # --- Status ---
        "is_active": True,    # False = account bị khóa (soft disable, không xóa)

        # --- Timestamps ---
        # Tại sao lưu timestamps? Để audit, debug, và sort theo thời gian
        "created_at": now,
        "updated_at": now,
    }
