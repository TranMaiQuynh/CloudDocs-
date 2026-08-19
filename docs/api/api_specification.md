# Đặc Tả API CloudDocs (API Specification v1)

Tài liệu này định nghĩa chi tiết danh sách các API Endpoint phục vụ cho dự án **CloudDocs - Collaborative Document Management System**.

---

## 1. Hướng Dẫn Chung

### Phiên Bản API
Tất cả các API được triển khai tại phiên bản v1 với tiền tố: `/api/v1`

### Xác Thực (Authentication)
Các API yêu cầu xác thực phải gửi kèm JWT Access Token trong header của HTTP request:
```http
Authorization: Bearer <your_access_token>
```

### Định Dạng Dữ Liệu (Data Format)
*   **Request Body:** `application/json` (Ngoại trừ các API Upload file sử dụng `multipart/form-data`).
*   **Response Body:** `application/json`
*   **Timezone:** Mọi mốc thời gian trả về đều sử dụng chuẩn UTC (ISO 8601): `YYYY-MM-DDTHH:MM:SSZ`

---

## 2. Danh Sách API Đăng Nhập & Xác Thực (`/api/v1/auth`)

Quản lý đăng ký, đăng nhập và thông tin tài khoản hiện hành.

### 2.1 Đăng ký tài khoản mới
*   **HTTP Method:** `POST`
*   **Path:** `/api/v1/auth/register`
*   **Authentication:** Không yêu cầu.
*   **Request Body (`application/json`):**
    ```json
    {
      "email": "student@university.edu.vn",
      "password": "SecurePassword123!",
      "full_name": "Trần Thị Lan"
    }
    ```
*   **Response (201 Created):**
    ```json
    {
      "success": true,
      "message": "Đăng ký tài khoản thành công!",
      "user": {
        "id": "64f1a2b3c4d5e6f7a8b9c0d1",
        "email": "student@university.edu.vn",
        "full_name": "Trần Thị Lan",
        "role": "member",
        "is_active": true,
        "created_at": "2026-08-15T12:00:00Z"
      }
    }
    ```

### 2.2 Đăng nhập hệ thống
*   **HTTP Method:** `POST`
*   **Path:** `/api/v1/auth/login`
*   **Authentication:** Không yêu cầu.
*   **Request Body (`application/json`):**
    ```json
    {
      "email": "student@university.edu.vn",
      "password": "SecurePassword123!"
    }
    ```
*   **Response (200 OK):**
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer",
      "expires_in": 3600,
      "user": {
        "id": "64f1a2b3c4d5e6f7a8b9c0d1",
        "email": "student@university.edu.vn",
        "full_name": "Trần Thị Lan",
        "role": "member",
        "is_active": true,
        "created_at": "2026-08-15T12:00:00Z"
      }
    }
    ```

### 2.3 Đăng xuất hệ thống
*   **HTTP Method:** `POST`
*   **Path:** `/api/v1/auth/logout`
*   **Authentication:** **Bắt buộc**.
*   **Response (200 OK):**
    ```json
    {
      "success": true,
      "message": "Đăng xuất thành công. Hẹn gặp lại, Trần Thị Lan!"
    }
    ```

### 2.4 Lấy thông tin tài khoản hiện tại
*   **HTTP Method:** `GET`
*   **Path:** `/api/v1/auth/me`
*   **Authentication:** **Bắt buộc**.
*   **Response (200 OK):**
    ```json
    {
      "id": "64f1a2b3c4d5e6f7a8b9c0d1",
      "email": "student@university.edu.vn",
      "full_name": "Trần Thị Lan",
      "role": "member",
      "is_active": true,
      "created_at": "2026-08-15T12:00:00Z"
    }
    ```

---

## 3. Danh Sách API Thư Mục (`/api/v1/folders`)

Quản lý cấu trúc thư mục lồng nhau lưu trên cơ sở dữ liệu MongoDB.

### 3.1 Tạo thư mục mới
*   **HTTP Method:** `POST`
*   **Path:** `/api/v1/folders`
*   **Authentication:** **Bắt buộc** (Admin, Leader).
*   **Request Body (`application/json`):**
    ```json
    {
      "name": "Báo cáo thực tập",
      "parent_id": "64f1a2b3c4d5e6f7a8b9c0a9", // Để null nếu tạo ở thư mục gốc
      "description": "Thư mục chứa tài liệu báo cáo thực tập tốt nghiệp"
    }
    ```
*   **Response (201 Created):**
    ```json
    {
      "id": "64f1a2b3c4d5e6f7a8b9c0ff",
      "name": "Báo cáo thực tập",
      "parent_id": "64f1a2b3c4d5e6f7a8b9c0a9",
      "created_by": "64f1a2b3c4d5e6f7a8b9c0d1",
      "description": "Thư mục chứa tài liệu báo cáo thực tập tốt nghiệp",
      "is_deleted": false,
      "created_at": "2026-08-15T13:00:00Z",
      "updated_at": "2026-08-15T13:00:00Z"
    }
    ```

### 3.2 Lấy danh sách thư mục & file hoạt động ở Root
*   **HTTP Method:** `GET`
*   **Path:** `/api/v1/folders`
*   **Authentication:** **Bắt buộc**.
*   **Query Parameters:**
    *   `page`: Số trang hiện tại (mặc định: 1)
    *   `limit`: Số lượng item trên một trang (mặc định: 20)
*   **Ghi chú:** API này chỉ trả về các thư mục và tài liệu có `is_deleted = false`.
*   **Response (200 OK):**
    ```json
    {
      "folders": [
        {
          "id": "64f1a2b3c4d5e6f7a8b9c0ff",
          "name": "Báo cáo thực tập",
          "created_by": "64f1a2b3c4d5e6f7a8b9c0d1",
          "created_at": "2026-08-15T13:00:00Z"
        }
      ],
      "documents": [
        {
          "id": "64f1a2b3c4d5e6f7a8b9c0ee",
          "name": "Đề cương chi tiết.pdf",
          "file_size": 1048576,
          "current_version": 1,
          "created_by": "64f1a2b3c4d5e6f7a8b9c0d1",
          "created_at": "2026-08-15T13:05:00Z"
        }
      ],
      "pagination": {
        "page": 1,
        "limit": 20,
        "total_folders": 1,
        "total_documents": 1
      }
    }
    ```

### 3.3 Truy cập và đọc nội dung bên trong một thư mục cụ thể
*   **HTTP Method:** `GET`
*   **Path:** `/api/v1/folders/{id}`
*   **Authentication:** **Bắt buộc**.
*   **Response (200 OK):** Trả về thông tin thư mục hiện tại kèm danh sách con tương tự mục 3.2 (loại trừ các phần tử đã xóa mềm).

### 3.4 Thay đổi thông tin thư mục (Đổi tên / Di chuyển vị trí cha con)
*   **HTTP Method:** `PATCH`
*   **Path:** `/api/v1/folders/{id}`
*   **Authentication:** **Bắt buộc** (Admin, Leader, Owner).
*   **Request Body (`application/json`):**
    ```json
    {
      "name": "Tên thư mục mới", // Optional
      "parent_id": "64f1a2b3c4d5e6f7a8b9c0aa", // Optional - để di chuyển folder
      "description": "Mô tả mới" // Optional
    }
    ```
*   **Response (200 OK):** Trả về thông tin chi tiết thư mục đã cập nhật.

### 3.5 Xóa mềm thư mục (Đưa vào Thùng rác)
*   **HTTP Method:** `DELETE`
*   **Path:** `/api/v1/folders/{id}`
*   **Authentication:** **Bắt buộc** (Admin, Leader, Owner).
*   **Mô tả:** Lệnh này thực hiện **Xóa mềm (Soft Delete)**. Cập nhật `is_deleted = true` và `deleted_at = current_time` cho thư mục hiện tại và đệ quy toàn bộ thư mục con & tài liệu nằm trong nó. Tài nguyên sẽ bị ẩn khỏi các API danh sách thông thường và chuyển vào thùng rác.
*   **Response (200 OK):**
    ```json
    {
      "success": true,
      "message": "Thư mục và toàn bộ nội dung con bên trong đã được chuyển vào thùng rác."
    }
    ```

---

## 4. Danh Sách API Tài Liệu (`/api/v1/documents`)

Tương tác với File Metadata lưu trong MongoDB và File vật lý lưu trên Supabase Storage.

### 4.1 Tải lên tài liệu mới
*   **HTTP Method:** `POST`
*   **Path:** `/api/v1/documents/upload`
*   **Authentication:** **Bắt buộc** (Admin, Leader).
*   **Request Headers:** `Content-Type: multipart/form-data`
*   **Request Body (Multipart Form):**
    *   `file`: Tệp tin vật lý (ví dụ: `Tailieu.pdf`).
    *   `folder_id`: ID của thư mục cha (string, để trống nếu upload ở thư mục gốc).
    *   `description`: Mô tả ngắn về file (string, optional).
*   **Response (201 Created):**
    ```json
    {
      "id": "64f1a2b3c4d5e6f7a8b9c0ee",
      "name": "Tailieu.pdf",
      "folder_id": "64f1a2b3c4d5e6f7a8b9c0ff",
      "storage_path": "users/64f1a2b3c4d5e6f7a8b9c0d1/folders/64f1a2b3c4d5e6f7a8b9c0ff/Tailieu.pdf",
      "file_size": 1048576,
      "mime_type": "application/pdf",
      "created_by": "64f1a2b3c4d5e6f7a8b9c0d1",
      "current_version": 1,
      "description": "Tài liệu mẫu",
      "is_deleted": false,
      "created_at": "2026-08-15T13:05:00Z"
    }
    ```

### 4.2 Lấy thông tin tài liệu
*   **HTTP Method:** `GET`
*   **Path:** `/api/v1/documents/{id}`
*   **Authentication:** **Bắt buộc**.
*   **Response (200 OK):** Trả về metadata chi tiết giống cấu trúc phản hồi API 4.1.

### 4.3 Sinh đường dẫn tải xuống tài liệu (Presigned URL)
*   **HTTP Method:** `GET`
*   **Path:** `/api/v1/documents/{id}/download`
*   **Authentication:** **Bắt buộc** (Viewer, Editor, Owner - hỗ trợ kiểm tra kế thừa quyền).
*   **Response (200 OK):**
    ```json
    {
      "download_url": "https://ftowtgdsewmjgupivsca.supabase.co/storage/v1/object/sign/documents/users/abc/Tailieu.pdf?token=...",
      "expires_in": 900 // Thời gian sống của link: 900 giây (15 phút)
    }
    ```

### 4.4 Cập nhật tài liệu (Đổi tên / Sửa mô tả / Di chuyển thư mục)
*   **HTTP Method:** `PATCH`
*   **Path:** `/api/v1/documents/{id}`
*   **Authentication:** **Bắt buộc** (Admin, Leader, Owner).
*   **Request Body (`application/json`):**
    ```json
    {
      "name": "Tên file mới.pdf", // Optional
      "folder_id": "64f1a2b3c4d5e6f7a8b9c0dd", // Optional - để di chuyển file
      "description": "Cập nhật mô tả mới" // Optional
    }
    ```
*   **Response (200 OK):** Trả về metadata tài liệu đã cập nhật.

### 4.5 Xóa mềm tài liệu (Đưa vào Thùng rác)
*   **HTTP Method:** `DELETE`
*   **Path:** `/api/v1/documents/{id}`
*   **Authentication:** **Bắt buộc** (Admin, Leader, Owner).
*   **Mô tả:** Lệnh này thực hiện **Xóa mềm (Soft Delete)**. Cập nhật `is_deleted = true` và `deleted_at = current_time` cho tài liệu để đưa vào thùng rác của cá nhân.
*   **Response (200 OK):**
    ```json
    {
      "success": true,
      "message": "Tài liệu đã được di chuyển vào thùng rác."
    }
    ```

---

## 5. Danh Sách API Lịch Sử Phiên Bản (`/api/v1/documents/{id}/versions`)

Quản lý nâng cấp các phiên bản ghi đè của một tài liệu.

### 5.1 Tải lên phiên bản mới của tài liệu
*   **HTTP Method:** `POST`
*   **Path:** `/api/v1/documents/{id}/versions`
*   **Authentication:** **Bắt buộc** (Editor, Owner).
*   **Request Headers:** `Content-Type: multipart/form-data`
*   **Request Body (Multipart Form):**
    *   `file`: File phiên bản mới.
    *   `change_log`: Nhật ký ghi chép các điểm thay đổi so với phiên bản cũ.
*   **Response (201 Created):**
    ```json
    {
      "success": true,
      "message": "Tải lên phiên bản mới thành công!",
      "new_version": {
        "document_id": "64f1a2b3c4d5e6f7a8b9c0ee",
        "version_number": 2,
        "storage_path": "users/64f1a2b3c4d5e6f7a8b9c0d1/versions/64f1a2b3c4d5e6f7a8b9c0ee_v2.pdf",
        "file_size": 1153433,
        "created_by": "64f1a2b3c4d5e6f7a8b9c0d1",
        "change_log": "Chỉnh sửa nội dung chương 2",
        "created_at": "2026-08-15T14:00:00Z"
      }
    }
    ```

### 5.2 Xem lịch sử các phiên bản
*   **HTTP Method:** `GET`
*   **Path:** `/api/v1/documents/{id}/versions`
*   **Authentication:** **Bắt buộc**.
*   **Response (200 OK):**
    ```json
    [
      {
        "version_number": 2,
        "file_size": 1153433,
        "created_by": "64f1a2b3c4d5e6f7a8b9c0d1",
        "change_log": "Chỉnh sửa nội dung chương 2",
        "created_at": "2026-08-15T14:00:00Z"
      },
      {
        "version_number": 1,
        "file_size": 1048576,
        "created_by": "64f1a2b3c4d5e6f7a8b9c0d1",
        "change_log": "Khởi tạo tài liệu gốc",
        "created_at": "2026-08-15T13:05:00Z"
      }
    ]
    ```

### 5.3 Tải xuống một phiên bản cũ cụ thể
*   **HTTP Method:** `GET`
*   **Path:** `/api/v1/documents/{id}/versions/{version_number}/download`
*   **Authentication:** **Bắt buộc**.
*   **Response (200 OK):** Trả về link Presigned URL tải file của phiên bản tương ứng giống mục 4.3.

---

## 6. Danh Sách API Thùng Rác & Khôi Phục (`/api/v1/trash`)

Quản lý khôi phục hoặc dọn sạch thùng rác vĩnh viễn (Cơ chế Soft Delete).

### 6.1 Lấy danh sách các tài nguyên đã bị xóa mềm
*   **HTTP Method:** `GET`
*   **Path:** `/api/v1/trash`
*   **Authentication:** **Bắt buộc**.
*   **Response (200 OK):**
    ```json
    {
      "folders": [
        {
          "id": "64f1a2b3c4d5e6f7a8b9c0ff",
          "name": "Báo cáo cũ",
          "deleted_at": "2026-08-15T14:30:00Z"
        }
      ],
      "documents": [
        {
          "id": "64f1a2b3c4d5e6f7a8b9c0ee",
          "name": "Nháp.docx",
          "deleted_at": "2026-08-15T14:35:00Z"
        }
      ]
    }
    ```

### 6.2 Khôi phục Thư mục
*   **HTTP Method:** `POST`
*   **Path:** `/api/v1/trash/folders/{id}/restore`
*   **Authentication:** **Bắt buộc** (Admin, Leader, Owner).
*   **Mô tả:** Đặt `is_deleted = false` và `deleted_at = null` cho thư mục hiện hành và đệ quy toàn bộ thư mục con & file con nằm dưới nó.
*   **Response (200 OK):**
    ```json
    {
      "success": true,
      "message": "Thư mục và các dữ liệu con đã được khôi phục thành công."
    }
    ```

### 6.3 Khôi phục Tài liệu
*   **HTTP Method:** `POST`
*   **Path:** `/api/v1/trash/documents/{id}/restore`
*   **Authentication:** **Bắt buộc** (Admin, Leader, Owner).
*   **Mô tả:** Đặt `is_deleted = false` và `deleted_at = null` cho tài liệu để phục hồi.
*   **Response (200 OK):**
    ```json
    {
      "success": true,
      "message": "Tài liệu đã được khôi phục thành công."
    }
    ```

### 6.4 Dọn sạch thùng rác vĩnh viễn (Xóa cứng)
*   **HTTP Method:** `DELETE`
*   **Path:** `/api/v1/trash/empty`
*   **Authentication:** **Bắt buộc** (Admin, Owner).
*   **Mô tả:** Xóa cứng hoàn toàn (Hard Delete) toàn bộ các thư mục và tài liệu có `is_deleted = true` của user hiện tại khỏi database MongoDB và tiến hành xóa file tương ứng trên Supabase Storage.
*   **Response (200 OK):**
    ```json
    {
      "success": true,
      "message": "Đã dọn sạch thùng rác và xóa vĩnh viễn toàn bộ tệp tin vật lý."
    }
    ```

---

## 7. Danh Sách API Chia Sẻ & Phân Quyền (`/api/v1/permissions`)

Quản lý quyền cộng tác viên và cơ chế kế thừa quyền (Permission Inheritance).

### Cơ chế Kế thừa Quyền (Permission Inheritance Model)
*   **Nguyên tắc:** Quyền được cấu hình tại Thư mục cha tự động áp dụng (kế thừa xuống) toàn bộ thư mục con và tài liệu nằm trong thư mục đó.
*   **Cách kiểm tra quyền tại Backend:**
    1.  Kiểm tra quyền trực tiếp cấu hình trên Tài liệu/Thư mục hiện hành ➡️ Nếu có, áp dụng ngay.
    2.  Nếu không có quyền trực tiếp, duyệt ngược cấu trúc cây (`parent_id`/`folder_id`) tìm quyền của User đó tại cấp độ cha gần nhất ➡️ Nếu tìm thấy, áp dụng quyền kế thừa.
    3.  Nếu không tìm thấy ở bất kỳ cấp độ nào và User không phải Owner/Admin ➡️ Từ chối truy cập (403 Forbidden).

### 7.1 Chia sẻ tài liệu/thư mục cho người dùng khác
*   **HTTP Method:** `POST`
*   **Path:** `/api/v1/permissions`
*   **Authentication:** **Bắt buộc** (Admin, Owner).
*   **Request Body (`application/json`):**
    ```json
    {
      "resource_id": "64f1a2b3c4d5e6f7a8b9c0ee",
      "resource_type": "document", // Hoặc "folder"
      "share_with_email": "colleague@university.edu.vn",
      "access_level": "editor" // Hoặc "viewer"
    }
    ```
*   **Response (201 Created):**
    ```json
    {
      "success": true,
      "message": "Đã chia sẻ quyền truy cập thành công với colleague@university.edu.vn.",
      "permission": {
        "id": "64f1a2b3c4d5e6f7a8b9c0ff",
        "resource_id": "64f1a2b3c4d5e6f7a8b9c0ee",
        "resource_type": "document",
        "user_id": "64f1a2b3c4d5e6f7a8b9c999", // ID của colleague
        "access_level": "editor",
        "granted_by": "64f1a2b3c4d5e6f7a8b9c0d1",
        "created_at": "2026-08-15T14:15:00Z"
      }
    }
    ```

### 7.2 Lấy danh sách những người được chia sẻ của một tài nguyên
*   **HTTP Method:** `GET`
*   **Path:** `/api/v1/permissions/resource/{resource_type}/{resource_id}`
*   **Authentication:** **Bắt buộc**.
*   **Response (200 OK):** Trả về danh sách những người dùng kèm quyền lợi của họ.

### 7.3 Thay đổi cấp độ quyền của cộng tác viên
*   **HTTP Method:** `PATCH`
*   **Path:** `/api/v1/permissions/{permission_id}`
*   **Authentication:** **Bắt buộc** (Admin, Owner).
*   **Request Body (`application/json`):**
    ```json
    {
      "access_level": "viewer" // Đổi từ editor xuống viewer
    }
    ```
*   **Response (200 OK):** Trả về thông tin quyền hạn đã cập nhật.

### 7.4 Hủy chia sẻ (Thu hồi quyền)
*   **HTTP Method:** `DELETE`
*   **Path:** `/api/v1/permissions/{permission_id}`
*   **Authentication:** **Bắt buộc** (Admin, Owner).
*   **Response (200 OK):**
    ```json
    {
      "success": true,
      "message": "Đã thu hồi quyền truy cập thành công."
    }
    ```

### 7.5 Lấy danh sách tài nguyên được người khác chia sẻ với tôi
*   **HTTP Method:** `GET`
*   **Path:** `/api/v1/shared`
*   **Authentication:** **Bắt buộc**.
*   **Response (200 OK):** Trả về danh sách thư mục & tệp tin được cấp quyền truy cập từ người khác.
