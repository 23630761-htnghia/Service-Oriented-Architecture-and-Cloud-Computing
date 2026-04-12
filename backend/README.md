# Backend

Thư mục này chứa toàn bộ backend của hệ thống Smart Livestream Management Platform.

## Services hiện có

- `services/api-gateway/`: cổng vào thống nhất cho frontend và client.
- `services/auth-service/`: auth demo với CAPTCHA và login.
- `services/account-service/`: quản lý dữ liệu user, livestream account, sản phẩm, nhà cung cấp và offer bằng SQLite.
- `services/ai-service/`: phân tích comment và cân bằng viewer.
- `services/sync-service/`: nhận comment qua API, gọi `ai-service` để enrich và lưu lịch sử sync trong memory.
- `services/report-service/`: tổng hợp KPI bằng cách gọi `account-service` và `sync-service`.

## Chạy nhanh backend

```bash
cd backend
docker compose up --build
```

Các cổng mặc định:

- `http://localhost:8000`: API Gateway
- `http://localhost:8001`: AI Service
- `http://localhost:8002`: Auth Service
- `http://localhost:8003`: Account Service
- `http://localhost:8004`: Sync Service
- `http://localhost:8005`: Report Service

## Gateway APIs chính

- `GET /health`
- `GET /api/v1/auth/captcha`
- `POST /api/v1/auth/login`
- `GET /api/v1/livestream-accounts`
- `POST /api/v1/comments/analyze`
- `POST /api/v1/streams/balance-viewers`
- `POST /api/v1/sync/comments`
- `GET /api/v1/sync/summary`
- `GET /api/v1/reports/kpis/overview`
- `GET /api/v1/reports/operations`

## Ghi chú

- `account-service` có dữ liệu seed SQLite sẵn trong `services/account-service/app/data/`.
- `sync-service` hiện chưa có database riêng.
- `report-service` chỉ tổng hợp từ API nội bộ của các service khác.
