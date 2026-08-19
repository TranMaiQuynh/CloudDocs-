"""
models/permission.py
====================
Mô tả:
    Đây là Data Model đại diện cho một Permission document trong MongoDB.
    Dùng để quản lý chia sẻ tài liệu/thư mục cho các người dùng khác nhau (Collaborators).

Quy tắc Kế thừa Quyền (Permission Inheritance Logic):
    1. Khi chia sẻ một Folder A cho User B với một quyền (AccessLevel), tất cả các Folder con 
       và Document con nằm bên trong Folder A sẽ tự động thừa kế quyền đó.
    2. Logic kiểm tra quyền của User đối với một Tài nguyên (Resource) bất kỳ:
       - Bước A: Kiểm tra xem có bản ghi Permission trực tiếp cho User đối với Resource đó không.
       - Bước B: Nếu không có bản ghi trực tiếp, duyệt ngược cấu trúc cây thư mục cha (`parent_id`/`folder_id`) 
         để tìm xem có bản ghi Permission nào của User đối với thư mục tổ tiên của nó không.
       - Bước C: Nếu tìm thấy ở bất kỳ cấp độ cha nào, áp dụng quyền đó cho tài nguyên hiện tại.
       - Bước D: Nếu không tìm thấy và User không phải Owner hoặc Admin, từ chối truy cập (403 Forbidden).
"""

from datetime import datetime, timezone
from enum import Enum
from bson import ObjectId


class AccessLevel(str, Enum):
    """
    Enum định nghĩa các cấp độ truy cập của người dùng được chia sẻ tài liệu.
    """
    VIEWER = "viewer"  # Chỉ được xem/tải xuống
    EDITOR = "editor"  # Được chỉnh sửa/tải lên phiên bản mới


def create_permission_document(
    resource_id: str,
    resource_type: str,
    user_id: str,
    access_level: AccessLevel = AccessLevel.VIEWER,
    granted_by: str = "",
    share_type: str = "user",
) -> dict:
    """
    Factory function tạo một permission document mới để lưu vào MongoDB.

    Args:
        resource_id:   ID của tài liệu (Document) hoặc thư mục (Folder) cần chia sẻ (string)
        resource_type: Loại tài nguyên ("document" hoặc "folder")
        user_id:       ID của người dùng hoặc nhóm học tập được chia sẻ (string)
        access_level:  Cấp độ quyền hạn truy cập (mặc định: AccessLevel.VIEWER)
        granted_by:    ID của người thực hiện chia sẻ (string)
        share_type:    Hình thức chia sẻ ("user" hoặc "group")

    Returns:
        dict: Document sẵn sàng để insert vào MongoDB collection "permissions"
    """
    now = datetime.now(timezone.utc)

    resource_oid = ObjectId(resource_id) if resource_id else None
    user_oid = ObjectId(user_id) if user_id else None
    granted_by_oid = ObjectId(granted_by) if granted_by else None

    return {
        "resource_id": resource_oid,
        "resource_type": resource_type.strip().lower(),  # "document" hoặc "folder"
        "user_id": user_oid,
        "share_type": share_type,
        "access_level": access_level.value,
        "granted_by": granted_by_oid,
        "created_at": now,
        "updated_at": now,
    }
