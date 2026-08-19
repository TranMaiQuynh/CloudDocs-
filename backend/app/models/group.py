"""
models/group.py
===============
Mô tả:
    Data Model đại diện cho một Nhóm học tập (Study Group) trong MongoDB.
"""

from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId
import uuid


def create_group_document(
    name: str,
    created_by: str,
    description: str = "",
    members: List[str] = [],
) -> dict:
    """
    Factory function tạo một study group document mới để lưu vào MongoDB.
    """
    now = datetime.now(timezone.utc)
    
    created_by_oid = ObjectId(created_by) if created_by else None
    
    member_oids = []
    # Thêm chủ nhóm làm thành viên mặc định
    if created_by:
        member_oids.append(created_by_oid)
        
    for m in members:
        try:
            m_oid = ObjectId(m)
            if m_oid not in member_oids:
                member_oids.append(m_oid)
        except Exception:
            pass

    # Tạo mã mời duy nhất (invite code) để chia sẻ qua link
    invite_code = uuid.uuid4().hex[:12]

    return {
        "name": name.strip(),
        "description": description.strip(),
        "created_by": created_by_oid,
        "members": member_oids,
        "invite_code": invite_code,
        "pending_members": [],
        "created_at": now,
        "updated_at": now,
    }
