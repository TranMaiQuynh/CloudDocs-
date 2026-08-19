from typing import Union, BinaryIO
from supabase import create_client
from app.core.config import settings

# Khởi tạo client Supabase kết nối Cloud Storage
supabase = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_KEY
)

# Mặc định bucket lưu trữ tài liệu của dự án là "documents"
BUCKET_NAME = "documents"


def upload_file(
    file_data: Union[bytes, BinaryIO],
    dest_path: str,
    content_type: str = "application/octet-stream"
) -> dict:
    """
    Upload tệp tin lên Supabase Storage bucket 'documents'.

    Args:
        file_data: Dữ liệu file dạng bytes hoặc file-like object (đọc từ UploadFile)
        dest_path: Đường dẫn lưu trữ đích trên bucket (ví dụ: 'users/123/tailieu.pdf')
        content_type: Định dạng MIME-type của file để hiển thị đúng khi download

    Returns:
        dict: Phản hồi từ Supabase Storage chứa metadata của file tải lên
    """
    # Sử dụng option x-upsert để ghi đè nếu trùng tên file (hữu ích cho quản lý phiên bản)
    file_options = {
        "content-type": content_type,
        "x-upsert": "true"
    }

    # Thực hiện tải lên
    response = supabase.storage.from_(BUCKET_NAME).upload(
        path=dest_path,
        file=file_data,
        file_options=file_options
    )
    return response


def download_file(storage_path: str) -> bytes:
    """
    Tải file vật lý từ Supabase Storage dạng raw bytes.

    Args:
        storage_path: Đường dẫn lưu trữ của file trên bucket

    Returns:
        bytes: Dữ liệu tệp tin dạng nhị phân
    """
    response = supabase.storage.from_(BUCKET_NAME).download(storage_path)
    return response


def delete_file(storage_path: str) -> dict:
    """
    Xóa file vật lý khỏi Supabase Storage.

    Args:
        storage_path: Đường dẫn lưu trữ của file trên bucket

    Returns:
        dict: Phản hồi kết quả xóa từ Supabase
    """
    # remove nhận vào một danh sách các đường dẫn cần xóa
    response = supabase.storage.from_(BUCKET_NAME).remove([storage_path])
    return response


def get_presigned_url(storage_path: str, expires_in: int = 3600) -> str:
    """
    Tạo một đường dẫn tải file tạm thời (Presigned URL) có giới hạn thời gian.
    Giúp bảo mật tệp tin, không để lộ link tải trực tiếp công khai.

    Args:
        storage_path: Đường dẫn lưu trữ của file trên bucket
        expires_in: Thời gian sống của link (giây, mặc định 3600s = 1 tiếng)

    Returns:
        str: Đường dẫn URL tải file bảo mật
    """
    response = supabase.storage.from_(BUCKET_NAME).create_signed_url(
        path=storage_path,
        expires_in=expires_in
    )

    # Lấy url từ phản hồi (supabase-py thường trả về dict chứa signedURL hoặc signedUrl)
    if isinstance(response, dict):
        url = response.get("signedURL") or response.get("signedUrl")
        if url:
            return url

    # Dự phòng nếu SDK trả về đối tượng/chuỗi khác
    if hasattr(response, "signed_url"):
        return getattr(response, "signed_url")
        
    return str(response)