"""
main.py
========
Mô tả:
    Entry point của FastAPI application.
    File này là nơi "lắp ráp" tất cả các thành phần lại với nhau.

Nhiệm vụ:
    1. Tạo FastAPI app instance
    2. Kết nối MongoDB khi khởi động (lifespan)
    3. Tạo indexes khi khởi động
    4. Register tất cả routers
    5. Cấu hình CORS (Cross-Origin Resource Sharing)

CORS là gì và tại sao cần?
    CORS = Cross-Origin Resource Sharing
    Browser chặn request từ domain A → domain B theo mặc định (Same-Origin Policy).
    Ví dụ: Frontend chạy ở localhost:5173 → Backend ở localhost:8000
    Browser sẽ chặn nếu không có CORS headers!

    Trong production:
    - allow_origins phải list cụ thể domain frontend (không dùng "*")
    - Dùng "*" trong dev để tiện test

Giao tiếp với:
    - database/connection.py   : client MongoDB để ping
    - repositories/user_repository: create_indexes()
    - routers/auth.py          : auth router

Uvicorn command:
    uvicorn app.main:app --reload
    (chạy từ thư mục backend/)
"""

from contextlib import asynccontextmanager
# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from app.database.connection import client
from app.core.config import settings
from app.repositories import (
    user_repository,
    folder_repository,
    document_repository,
    version_repository,
    permission_repository,
)
from app.routers import auth, folders, documents, permissions, versions, comments, activities, groups, notifications


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager: code chạy khi app START và STOP.

    Thay thế @app.on_event("startup") và @app.on_event("shutdown") cũ.
    Code trước `yield` chạy khi startup.
    Code sau `yield` chạy khi shutdown.

    Tại sao kiểm tra kết nối khi startup?
    - Phát hiện lỗi config ngay từ đầu, không phải đến khi có request
    - Dễ debug: thấy "[SUCCESS] Connected" trong log → biết DB ok
    """
    # ── STARTUP ──────────────────────────────────────────
    print("\n" + "="*50)
    print("  CloudDocs API Starting...")
    print("="*50)

    # Kiểm tra kết nối MongoDB
    try:
        await client.admin.command("ping")
        print("MongoDB Atlas: Connected")
    except Exception as e:
        print(f"MongoDB Atlas: Connection FAILED!")
        print(f"   Error: {e}")
        print("   Kiểm tra MONGODB_URI trong file .env")

    # Tạo database indexes
    # Gọi sau khi confirm kết nối thành công
    try:
        await user_repository.create_indexes()
        await folder_repository.create_indexes()
        await document_repository.create_indexes()
        await version_repository.create_indexes()
        await permission_repository.create_indexes()
        print("MongoDB Indexes: Created/Verified")
    except Exception as e:
        print(f"MongoDB Indexes: {e}")

    print(f"Database: {settings.DATABASE_NAME}")
    print("="*50)
    print("  API is ready! Visit /docs for Swagger UI")
    print("="*50 + "\n")

    yield  # ← App đang chạy

    # ── SHUTDOWN ─────────────────────────────────────────
    client.close()
    print("\nMongoDB connection closed. Goodbye!")


# Tạo FastAPI app instance
app = FastAPI(
    title="CloudDocs API",
    version="1.0.0",
    description="""
## Cloud-based Collaborative Document Management System

Hệ thống quản lý tài liệu nhóm học tập trên Cloud.

### Features
* **Authentication**: Đăng ký, đăng nhập, đăng xuất với JWT
* **Authorization**: RBAC với 3 roles: Admin, Leader, Member
* **Document Management**: Upload, download, rename, delete, search
* **Version Control**: Quản lý phiên bản tài liệu cơ bản
* **Cloud Storage**: Lưu file trên Supabase Storage
* **NoSQL Database**: Metadata lưu trên MongoDB Atlas

### Authentication
Sau khi đăng nhập, thêm token vào header:
```
Authorization: Bearer <your_access_token>
```
    """,
    contact={
        "name": "CloudDocs Team",
        "email": "clouddocs@university.edu.vn",
    },
    license_info={
        "name": "MIT",
    },
)


# ── CORS Middleware ───────────────────────────────────────────────────────────
"""
Cấu hình CORS cho phép Frontend gọi API.

allow_origins: Các domain được phép gọi API
  - Development: ["*"] hoặc ["http://localhost:5173"]
  - Production: ["https://your-frontend.vercel.app"]

allow_methods: Các HTTP methods được phép
allow_headers: Các headers được phép (phải có "Authorization" cho JWT)
allow_credentials: True nếu dùng cookies (chúng ta dùng JWT nên False)
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],   # GET, POST, PUT, DELETE, OPTIONS, PATCH
    allow_headers=["*"],   # Authorization, Content-Type, v.v.
)

from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"}
    )


# ── Register Routers ──────────────────────────────────────────────────────────
"""
Include routers vào app.
Mỗi router có prefix riêng và tags cho Swagger UI.
"""
app.include_router(auth.router)
app.include_router(folders.router)
app.include_router(documents.router)
app.include_router(permissions.router)
app.include_router(versions.router)
app.include_router(comments.router)
app.include_router(activities.router)
app.include_router(groups.router)
app.include_router(notifications.router)


# ── Root Endpoint ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health Check"], summary="API Health Check")
async def root():
    """
    Health check endpoint.
    Dùng để verify API đang chạy (monitoring, load balancer check, v.v.)
    """
    return {
        "message": "CloudDocs API is running!",
        "version": "1.0.0",
        "docs": "/docs",          # Swagger UI
        "redoc": "/redoc",        # ReDoc documentation
    }


@app.get("/health", tags=["Health Check"], summary="Detailed Health Check")
async def health_check():
    """Detailed health check với database status."""
    try:
        await client.admin.command("ping")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "version": "1.0.0",
    }