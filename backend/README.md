# Backend

Thư mục `backend/` chứa toàn bộ các service phía server của hệ thống Smart Livestream Management Platform.

## 1. Các service hiện có

- `services/api-gateway/`: cổng vào thống nhất cho app quản lý và app demo
- `services/auth-service/`: cấp CAPTCHA và xử lý đăng nhập
- `services/account-service/`: quản lý user nội bộ, khách hàng, giỏ hàng, đơn hàng, bình luận, hội thoại và cấu hình AI
- `services/catalog-service/`: quản lý sản phẩm, nhà cung cấp và supplier offers
- `services/livestream-service/`: quản lý phòng livestream, phân công sản phẩm, live offer, presence viewer và trạng thái live
- `services/ai-service/`: phân tích bình luận để nhận diện mức độ quan tâm của khách hàng
- `services/sync-service/`: đồng bộ và enrich dữ liệu comment mẫu
- `services/report-service/`: tổng hợp dữ liệu và KPI từ nhiều service

## 2. Vai trò của backend trong bài hiện tại

Backend là lớp dùng chung cho cả 2 ứng dụng:

- `frontend/` dùng backend để quản lý tài khoản, phòng live, sản phẩm, nhà cung cấp và cấu hình AI
- `apps/demo-app/` dùng backend để lấy dữ liệu live thật, sản phẩm, comment, message, cart, order và viewer presence

Điều này có nghĩa là dữ liệu giữa app quản lý và app demo không chạy độc lập, mà được đồng bộ qua cùng một lớp service.

## 3. Chạy backend bằng Docker

```bash
cd backend
docker compose up --build
```

Hoặc chạy toàn bộ hệ thống:

```bash
cd infra/docker
docker compose up --build
```

## 4. Cổng mặc định

- `8000`: API Gateway
- `8001`: AI Service
- `8002`: Auth Service
- `8003`: Account Service
- `8004`: Sync Service
- `8005`: Report Service
- `8006`: Catalog Service
- `8007`: Livestream Service

## 5. API chính qua Gateway

- `GET /health`
- `GET /api/v1/auth/captcha`
- `POST /api/v1/auth/login`
- `GET /api/v1/database-overview`
- `GET /api/v1/livestream-accounts`
- `POST /api/v1/livestream-comments`
- `POST /api/v1/livestream-messages`
- `GET /api/v1/customers`
- `POST /api/v1/customers/register`
- `GET /api/v1/customers/{customer_id}/cart`
- `POST /api/v1/customers/{customer_id}/cart/items`
- `POST /api/v1/customers/{customer_id}/checkout`
- `GET /api/v1/ai-assistant/settings`
- `PATCH /api/v1/ai-assistant/settings`

## 6. Dữ liệu và đồng bộ

- `account-service`, `catalog-service` và `livestream-service` đang dùng dữ liệu seed + SQLite cho mục tiêu học tập và demo
- `demo-app` không còn giữ dữ liệu chính ở local như customer, cart hay product; các dữ liệu này đều đi qua backend
- Viewer realtime được tính theo presence/heartbeat từ client thật

## 7. Ghi chú

- App quản lý chỉ cho phép `admin` và `quản lý sản phẩm` đăng nhập
- App demo dùng các vai trò `nhân viên bán hàng` và `khách hàng`
- AI trong bài hiện tại dùng để phân tích comment và mở đầu hội thoại, còn phần tư vấn tiếp theo do nhân viên trả lời
