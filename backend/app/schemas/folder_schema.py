"""
schemas/folder_schema.py
========================
Mô tả:
    Pydantic schemas kiểm soát dữ liệu vào/ra API cho Folder.
    FastAPI tự động validate và serialize dựa trên các schema này.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class FolderCreateRequest(BaseModel):
    """
    Schema cho POST /folders.
    Dữ liệu client gửi lên để tạo thư mục mới.
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Tên thư mục",
        examples=["Đồ án tốt nghiệp"]
    )
    parent_id: Optional[str] = Field(
        default=None,
        description="ID của thư mục cha, để null nếu là thư mục gốc"
    )
    description: Optional[str] = Field(
        default="",
        max_length=500,
        description="Mô tả chi tiết về thư mục"
    )
    tags: List[str] = Field(
        default=[],
        description="Danh sách các nhãn môn học/phân loại thư mục"
    )

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        """
        Kiểm tra tên không được chứa ký tự trống hoặc chỉ dấu cách.
        """
        if not v.strip():
            raise ValueError("Tên thư mục không được để trống")
        return v.strip()


class FolderUpdateRequest(BaseModel):
    """
    Schema cho PATCH /folders/{folder_id}.
    Dữ liệu client gửi lên để cập nhật (đổi tên, sửa mô tả, di chuyển vị trí) thư mục.
    """
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Tên mới của thư mục",
        examples=["Đồ án tốt nghiệp - Phiên bản 2"]
    )
    parent_id: Optional[str] = Field(
        default=None,
        description="ID của thư mục cha mới (nếu muốn di chuyển)"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Mô tả mới của thư mục"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Danh sách nhãn phân loại mới"
    )

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Tên thư mục không được để trống")
        return v.strip() if v is not None else None


class FolderResponse(BaseModel):
    """
    Schema trả về thông tin chi tiết của Folder.
    """
    id: str = Field(description="ID của thư mục (MongoDB ObjectId dạng string)")
    name: str = Field(description="Tên thư mục")
    parent_id: Optional[str] = Field(description="ID của thư mục cha (string hoặc null)")
    created_by: str = Field(description="ID của người tạo thư mục")
    description: Optional[str] = Field(default="", description="Mô tả thư mục")
    is_deleted: bool = Field(default=False, description="Trạng thái xóa mềm")
    tags: List[str] = Field(default=[], description="Danh sách các nhãn phân loại")
    created_at: datetime = Field(description="Thời gian tạo")
    updated_at: datetime = Field(description="Thời gian cập nhật")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "64f2b3c4d5e6f7a8b9c0d1e2",
                "name": "Đồ án tốt nghiệp",
                "parent_id": None,
                "created_by": "64f1a2b3c4d5e6f7a8b9c0d1",
                "description": "Thư mục chứa tài liệu tốt nghiệp",
                "is_deleted": False,
                "created_at": "2026-08-15T11:00:00Z",
                "updated_at": "2026-08-15T11:00:00Z"
            }
        }
    }
