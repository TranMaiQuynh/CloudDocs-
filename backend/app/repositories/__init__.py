# Repositories package
# Import các repository để dùng tiện hơn
from app.repositories import user_repository
from app.repositories import folder_repository
from app.repositories import document_repository
from app.repositories import version_repository
from app.repositories import permission_repository

__all__ = [
    "user_repository",
    "folder_repository",
    "document_repository",
    "version_repository",
    "permission_repository",
]
