# Smart Livestream Management Platform

## 1. Giới thiệu

Đây là đồ án xây dựng hệ thống quản lý nhiều tài khoản livestream theo hướng service-oriented architecture. Hệ thống tập trung vào 4 bài toán chính:

- quản lý tập trung nhiều tài khoản livestream theo từng nền tảng,
- đồng bộ comment và phân tích comment bằng AI,
- gợi ý cân bằng viewer để giảm nguy cơ lag,
- tổng hợp KPI và báo cáo vận hành.

Trong trạng thái hiện tại của repo, hệ thống đang ở mức demo kỹ thuật và mô phỏng nghiệp vụ. `sync-service` nhận comment qua API nội bộ, gọi `ai-service` để enrich dữ liệu và `report-service` tổng hợp KPI cho dashboard.

## 2. Công nghệ và phiên bản

### Ngôn ngữ sử dụng

- Python
- HTML
- CSS
- JavaScript

### Phiên bản và framework chính

- Python runtime trong Docker: `3.11-slim`
- FastAPI: `0.115.0`
- Uvicorn: `0.30.6`
- Pydantic: `2.9.2`
- scikit-learn: `1.5.2`
- pandas: `2.2.3`
- joblib: `1.4.2`
- SQLite: dùng cho `account-service`
- Docker Compose: dùng để chạy nhanh toàn bộ stack

### Thành phần giao diện và dữ liệu

- Frontend là trang tĩnh viết bằng `HTML/CSS/JavaScript`.
- Backend là các microservice `FastAPI`.
- ML dùng mô hình `scikit-learn` để phân loại `intent` và `sentiment`.
- Dữ liệu quản trị hiện dùng `SQLite` và JSON seed.

## 3. Chức năng hiện có

- Đăng nhập demo với CAPTCHA.
- Quản lý user, tài khoản livestream, sản phẩm, nhà cung cấp và offer.
- Phân tích comment theo `intent`, `sentiment`, `lead_score`, `priority`.
- Phân tích batch comment.
- Gợi ý cân bằng viewer giữa các room livestream.
- Đồng bộ comment qua `sync-service`.
- Tổng hợp KPI và báo cáo vận hành qua `report-service`.

## 4. Kiến trúc hiện tại

### Backend services

- `api-gateway`: đầu vào thống nhất cho frontend và client.
- `auth-service`: login demo và CAPTCHA.
- `account-service`: quản lý dữ liệu nghiệp vụ bằng SQLite.
- `ai-service`: phân tích comment và viewer balancing.
- `sync-service`: nhận comment, enrich bằng AI, lưu lịch sử sync trong memory và hỗ trợ export.
- `report-service`: gom dữ liệu từ các service khác để tạo KPI và báo cáo.

### Frontend

- `frontend/`: dashboard tĩnh gọi API qua gateway.

### ML

- `ml/training/train_comment_models.py`: train lại model `intent` và `sentiment`.
- `ml/models/`: nơi lưu model đã train.

## 5. Cấu trúc repo

```text
frontend/                     Dashboard tĩnh
backend/services/             Các microservice FastAPI
ml/                           Dữ liệu gán nhãn, script train, model
infra/docker/                 Docker Compose cho toàn bộ hệ thống
docs/                         Tài liệu kiến trúc và triển khai
```

## 6. Cách chạy nhanh

### Cách 1: chạy toàn bộ hệ thống bằng Docker Compose

```bash
cd infra/docker
docker compose up --build
```

- Frontend: `http://localhost:3000`
- API Gateway: `http://localhost:8000`
- AI Service: `http://localhost:8001`
- Auth Service: `http://localhost:8002`
- Account Service: `http://localhost:8003`
- Sync Service: `http://localhost:8004`
- Report Service: `http://localhost:8005`

```bash
cd infra/docker
docker compose up --build
```

Dừng hệ thống:

```bash
cd infra/docker
docker compose down
```

### Cách 2: chạy riêng backend

```bash
cd backend
docker compose up --build
```

## 7. Các bước demo chung

### Luồng demo local

1. Chạy hệ thống bằng Docker Compose.
2. Mở `http://localhost:8000/health` hoặc `http://localhost:8000/docs` để kiểm tra gateway đã sẵn sàng.
3. Đăng nhập frontend bằng tài khoản mẫu.
4. Gọi sync comment qua gateway hoặc dùng giao diện dashboard.
5. Xem kết quả AI analysis và KPI report.
6. Kiểm tra thêm các API báo cáo nếu cần.

### Train lại model AI

```bash
pip install -r backend/services/ai-service/requirements.txt
python ml/training/train_comment_models.py
```

Sau khi train xong:

- `ml/models/intent_model.joblib`
- `ml/models/sentiment_model.joblib`
- `ml/models/metrics.json`

Nếu chưa có model, `ai-service` sẽ fallback về rule-based analyzer.

## 8. Tài khoản mẫu

- Admin: `admin@smartlive.vn` / `123456`
- Staff: `staff@smartlive.vn` / `staff01`
- Staff 02: `staff02@smartlive.vn` / `staff02`
- Staff 03: `staff03@smartlive.vn` / `staff03`
- Staff 04: `staff04@smartlive.vn` / `staff04`

## 9. API chính qua gateway

### Health

- `GET /health`

### Auth

- `GET /api/v1/auth/captcha`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### Account

- `GET /api/v1/users`
- `POST /api/v1/users/staff`
- `PATCH /api/v1/users/{user_id}/password`
- `GET /api/v1/livestream-accounts`
- `GET /api/v1/livestream-accounts/grouped`
- `GET /api/v1/platform-summaries`
- `GET /api/v1/platforms/{platform}/accounts`
- `POST /api/v1/livestream-accounts`
- `GET /api/v1/products`
- `POST /api/v1/products`
- `PATCH /api/v1/products/{product_id}`
- `DELETE /api/v1/products/{product_id}`
- `GET /api/v1/suppliers`
- `POST /api/v1/suppliers`
- `PATCH /api/v1/suppliers/{supplier_id}`
- `DELETE /api/v1/suppliers/{supplier_id}`
- `GET /api/v1/supplier-offers`
- `GET /api/v1/database-overview`

### AI

- `POST /api/v1/comments/analyze`
- `POST /api/v1/comments/analyze-batch`
- `POST /api/v1/streams/balance-viewers`
- `POST /api/v1/streams/session-optimizer`

### Sync

- `GET /api/v1/sync/jobs`
- `GET /api/v1/sync/summary`
- `GET /api/v1/sync/records`
- `POST /api/v1/sync/comments`
- `POST /api/v1/sync/comments/batch`

### Reports

- `GET /api/v1/reports/kpis/overview`
- `GET /api/v1/reports/operations`

## 10. Giới hạn hiện tại

- `sync-service` hiện lưu lịch sử sync trong memory, chưa dùng database riêng.
- Dữ liệu comment hiện được sync qua API demo nội bộ, chưa nối trực tiếp API thật từ TikTok/Facebook.

## 11. Tài liệu liên quan

- [Backend README](backend/README.md)
- [ML README](ml/README.md)
- [Kiến trúc hệ thống](docs/architecture.md)
- [AI analysis](docs/ai-analysis.md)
- [Use cases](docs/use-cases.md)
