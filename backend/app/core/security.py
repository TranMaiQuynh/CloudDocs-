"""
core/security.py
================
Mô tả:
    "Hộp công cụ bảo mật" — chứa tất cả logic mã hóa tập trung ở 1 nơi.

    Có 2 nhóm công cụ:
    1. Password tools  : hash và verify password bằng bcrypt
    2. JWT tools       : tạo và giải mã JWT token

Tại sao tập trung vào 1 file?
    - DRY (Don't Repeat Yourself): không viết lại logic bcrypt ở nhiều chỗ
    - SRP (Single Responsibility): file này chỉ làm 1 việc = bảo mật
    - Dễ thay thế: muốn đổi từ bcrypt sang argon2? Chỉ sửa 1 file này
    - Dễ test: import và test từng function riêng lẻ

Giao tiếp với:
    - services/auth_service.py : gọi hash_password() khi register
                                 gọi verify_password() khi login
                                 gọi create_access_token() sau khi login thành công
    - dependencies/auth_deps.py: gọi decode_access_token() để verify JWT

Libraries:
    - passlib[bcrypt]: bcrypt implementation chuẩn, được audit bảo mật
    - python-jose[cryptography]: JWT implementation chuẩn cho Python
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
# pyrefly: ignore [missing-import]
from jose import JWTError, jwt
# pyrefly: ignore [missing-import]
from passlib.context import CryptContext
from app.core.config import settings


# ============================================================
# BCRYPT CONFIGURATION
# ============================================================

"""
CryptContext: "ngữ cảnh mã hóa" — quản lý thuật toán hash.

Tại sao dùng CryptContext thay vì gọi bcrypt trực tiếp?
- Hỗ trợ "deprecated schemes": nếu sau này muốn migrate từ bcrypt
  sang argon2, CryptContext tự động re-hash password cũ khi user login.
- Abstraction layer: code gọi pwd_context.hash() thay vì bcrypt.hashpw()
  → dễ swap thuật toán mà không sửa nhiều chỗ.

schemes=["bcrypt"]: dùng bcrypt làm thuật toán chính.
deprecated="auto": các scheme cũ hơn (nếu có) tự động bị deprecated.
"""
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============================================================
# JWT CONFIGURATION
# ============================================================

"""
Giải thích các hằng số JWT:

ALGORITHM = "HS256"
    - HS256 = HMAC + SHA-256
    - HMAC: Hash-based Message Authentication Code
    - Dùng 1 secret key để cả ký lẫn verify → "symmetric"
    - Ưu điểm: đơn giản, nhanh
    - Nhược điểm: server phải biết secret key → không chia sẻ được với bên thứ 3
    - Đủ tốt cho dự án này (single server)
    - Alternative: RS256 (asymmetric) — dùng khi nhiều services cần verify token

ACCESS_TOKEN_EXPIRE_MINUTES = 60
    - Token hết hạn sau 60 phút
    - Trade-off: ngắn = an toàn hơn nhưng user phải login lại thường
    - Production: dùng thêm refresh token (7 days) + access token (15 mins)
    - Cho dự án này: 60 phút là hợp lý
"""
ALGORITHM = "HS256"
# Lấy từ cấu hình settings
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


# ============================================================
# PASSWORD FUNCTIONS
# ============================================================

def hash_password(plain_password: str) -> str:
    """
    Hash password bằng bcrypt.

    Tại sao không lưu plain_password?
    - Nếu DB bị hack, attacker không có password thật của users
    - GDPR / bảo mật pháp lý: phải mã hóa thông tin nhạy cảm
    - bcrypt tự động thêm salt ngẫu nhiên → mỗi lần hash ra chuỗi khác nhau

    Args:
        plain_password: Mật khẩu dạng plaintext từ user

    Returns:
        str: Chuỗi bcrypt hash (ví dụ: "$2b$12$eImiTXuWVx...")

    Ví dụ:
        hash_password("mypass123") → "$2b$12$abc..."
        hash_password("mypass123") → "$2b$12$xyz..."  ← KHÁC! Do salt ngẫu nhiên
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Kiểm tra password có khớp với hash không.

    Tại sao không hash rồi so sánh?
    - bcrypt hash có salt ngẫu nhiên embedded trong chuỗi hash
    - pwd_context.verify() tự extract salt từ hash, rồi hash password với salt đó
    - Nếu tự hash và so sánh sẽ LUÔN KHÁC vì salt khác nhau

    Args:
        plain_password:  Mật khẩu user vừa nhập khi login
        hashed_password: Hash lưu trong DB

    Returns:
        bool: True nếu password đúng, False nếu sai

    Ví dụ:
        stored = "$2b$12$abc..."  (hash của "mypass123")
        verify_password("mypass123", stored) → True
        verify_password("wrongpass", stored) → False
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================
# JWT FUNCTIONS
# ============================================================

def create_access_token(
    user_id: str,
    role: str,
    email: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Tạo JWT access token sau khi user login thành công.

    Cấu trúc payload:
        sub   = subject (user_id) — định danh chính của token
        role  = role của user — dùng để phân quyền mà không cần query DB
        email = email — tiện cho logging và debugging
        exp   = expiry time — server tự động reject token hết hạn
        iat   = issued at — khi nào token được tạo (cho audit)

    Tại sao lưu role trong token?
    - Không cần query DB mỗi request để biết quyền của user
    - Stateless: server không lưu gì, chỉ verify chữ ký
    - Trade-off: nếu role của user thay đổi, token cũ vẫn có role cũ
      → Chấp nhận được vì token chỉ sống 60 phút

    Args:
        user_id:       MongoDB ObjectId của user (dạng string)
        role:          Role của user ("admin"/"leader"/"member")
        email:         Email của user
        expires_delta: Thời gian sống của token (mặc định 60 phút)

    Returns:
        str: JWT token (3 phần ngăn bởi dấu chấm)
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": user_id,        # Subject: user ID (required by JWT standard)
        "role": role,           # Custom claim: role cho RBAC
        "email": email,         # Custom claim: email cho logging
        "exp": expire,          # Expiry: jose tự convert datetime → Unix timestamp
        "iat": now,             # Issued At: khi nào token được tạo
    }

    """
    jwt.encode() ký payload bằng secret key + thuật toán HS256.
    Kết quả là chuỗi: "<header_b64>.<payload_b64>.<signature>"
    
    settings.JWT_SECRET_KEY phải là chuỗi ngẫu nhiên dài, bí mật.
    Nếu bị lộ, attacker có thể tạo token giả với bất kỳ role nào!
    """
    encoded_jwt = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Giải mã và verify JWT token từ request header.

    Quá trình verify:
    1. Tách token thành 3 phần (header, payload, signature)
    2. Dùng secret key và ALGORITHM để verify signature
    3. Kiểm tra exp chưa hết hạn
    4. Nếu ok → trả payload dict; Nếu fail → trả None

    Tại sao trả None thay vì raise Exception?
    - Để caller (dependencies/auth_deps.py) quyết định cách handle lỗi
    - Tách biệt "decode logic" và "HTTP error handling"

    Args:
        token: JWT string từ Authorization header

    Returns:
        dict | None: Payload dict nếu valid, None nếu invalid/expired

    Ví dụ payload trả về:
        {
            "sub": "64f1a2b3c4d5e6f7a8b9c0d1",
            "role": "member",
            "email": "student@university.edu.vn",
            "exp": 1700000000,
            "iat": 1699996400
        }
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        # JWTError bao gồm: token invalid, signature mismatch, token expired
        return None


def create_refresh_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Tạo JWT refresh token sau khi user login thành công.

    Refresh token có thời gian sống lâu hơn (mặc định 7 ngày)
    và chỉ chứa tối thiểu payload để đảm bảo an toàn.
    """
    if expires_delta is None:
        expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": user_id,
        "type": "refresh",  # Phân biệt rõ loại token
        "exp": expire,
        "iat": now,
    }

    encoded_jwt = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

