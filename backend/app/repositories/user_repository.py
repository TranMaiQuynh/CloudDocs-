"""
repositories/user_repository.py
================================
Mô tả:
    Data Access Layer — tất cả câu query MongoDB liên quan đến User tập trung ở đây.

Tại sao cần Repository Pattern?
    Vấn đề nếu không có:
        - Service phải biết collection name là "users"
        - Service phải viết query MongoDB trực tiếp
        - Nếu đổi DB → phải sửa tất cả Service files

    Với Repository:
        - Service chỉ gọi: await user_repo.find_by_email("a@b.com")
        - Service không biết đây là MongoDB, PostgreSQL hay gì
        - Đổi DB → chỉ sửa repository file này

Design Pattern:
    Repository Pattern — tách biệt "business logic" và "data access logic"

Giao tiếp với:
    - database/connection.py : lấy database object để query
    - models/user.py         : dùng create_user_document() factory
    - services/auth_service  : gọi các method của repo này

MongoDB Collection: "users"
Indexes cần thiết:
    - email (unique): tìm user theo email nhanh, đảm bảo email duy nhất
"""

from typing import Optional
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from app.database.connection import database
from app.models.user import create_user_document, UserRole


# Lấy collection "users" từ database
# Convention: tên collection viết thường, số nhiều
users_collection = database["users"]


async def create_indexes() -> None:
    """
    Tạo MongoDB indexes cho collection users.

    Tại sao cần indexes?
    - Không có index: MongoDB scan TOÀN BỘ collection để tìm (O(n))
    - Có index: MongoDB dùng B-tree để tìm cực nhanh (O(log n))

    Unique index trên email:
    - Đảm bảo không có 2 user cùng email (database-level constraint)
    - Nếu insert duplicate → MongoDB raise DuplicateKeyError
    - Tốt hơn chỉ check bằng code (race condition safe)

    Khi nào gọi hàm này?
    - Khi app khởi động (trong main.py lifespan)
    - MongoDB chỉ tạo index nếu chưa tồn tại → an toàn gọi nhiều lần
    """
    await users_collection.create_index("email", unique=True)


async def find_by_email(email: str) -> Optional[dict]:
    """
    Tìm user theo email (dùng khi login và check email đã tồn tại).

    Tại sao normalize email?
    - "User@Email.COM" và "user@email.com" phải là cùng 1 user
    - Normalize khi tìm kiếm phải khớp với normalize khi lưu

    Args:
        email: Email của user cần tìm

    Returns:
        dict | None: User document nếu tìm thấy, None nếu không có
    """
    return await users_collection.find_one({"email": email.lower().strip()})


async def find_by_id(user_id: str) -> Optional[dict]:
    """
    Tìm user theo MongoDB ObjectId.

    Tại sao phải convert string → ObjectId?
    - MongoDB lưu _id là ObjectId (12-byte binary), không phải string
    - API nhận string → phải convert trước khi query
    - Nếu string không hợp lệ → InvalidId exception

    Args:
        user_id: MongoDB ObjectId dạng string (24 hex characters)

    Returns:
        dict | None: User document nếu tìm thấy, None nếu không có
    """
    try:
        oid = ObjectId(user_id)
    except InvalidId:
        # user_id không phải format ObjectId hợp lệ
        return None

    return await users_collection.find_one({"_id": oid})


async def create_user(
    email: str,
    hashed_password: str,
    full_name: str,
    role: UserRole = UserRole.MEMBER,
) -> dict:
    """
    Tạo user mới trong MongoDB.

    Luồng:
    1. Dùng factory function để tạo document dict
    2. insert_one() → MongoDB trả về InsertOneResult với inserted_id
    3. find_one() lại để lấy document đầy đủ (bao gồm _id đã được MongoDB gán)

    Tại sao find_one lại sau insert?
    - insert_one trả về InsertOneResult, không phải document đầy đủ
    - Chỉ có inserted_id, không có các fields khác
    - Cần return document đầy đủ để service tạo JWT token

    Args:
        email:           Email đã được normalize
        hashed_password: bcrypt hash của password
        full_name:       Tên đầy đủ
        role:            UserRole enum (mặc định MEMBER)

    Returns:
        dict: User document đầy đủ bao gồm _id

    Raises:
        DuplicateKeyError: Nếu email đã tồn tại (unique index constraint)
    """
    user_doc = create_user_document(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        role=role,
    )

    result = await users_collection.insert_one(user_doc)

    # Lấy lại document đầy đủ với _id
    created_user = await users_collection.find_one({"_id": result.inserted_id})
    return created_user


async def update_user(user_id: str, update_data: dict) -> Optional[dict]:
    """
    Cập nhật thông tin user (dùng cho admin quản lý user sau này).

    $set operator: chỉ update các fields được chỉ định, không xóa các field khác.
    Ví dụ: $set {"full_name": "Tên mới"} chỉ update full_name, giữ nguyên email, role.

    Args:
        user_id:     MongoDB ObjectId dạng string
        update_data: Dict chứa các fields cần update

    Returns:
        dict | None: User document đã được update, None nếu không tìm thấy
    """
    try:
        oid = ObjectId(user_id)
    except InvalidId:
        return None

    # Luôn cập nhật updated_at khi sửa bất kỳ field nào
    update_data["updated_at"] = datetime.now(timezone.utc)

    await users_collection.update_one(
        {"_id": oid},
        {"$set": update_data}
    )

    return await users_collection.find_one({"_id": oid})


def format_user_id(user: dict) -> dict:
    """
    Helper: convert MongoDB ObjectId sang string để trả về JSON.

    Vấn đề:
        MongoDB document: {"_id": ObjectId("64f1a2b3..."), "email": "..."}
        JSON không serialize ObjectId → TypeError!

    Giải pháp:
        Convert ObjectId → string, đổi key "_id" → "id" (convention cho REST API)

    Args:
        user: MongoDB document có _id là ObjectId

    Returns:
        dict: Document với "id" là string thay vì "_id" là ObjectId
    """
    user_copy = dict(user)
    if "_id" in user_copy:
        user_copy["id"] = str(user_copy.pop("_id"))
    return user_copy
