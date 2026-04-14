# Backend

Thư mục này chứa toàn bộ backend của hệ thống Smart Livestream Management Platform.

## Services hiện có

- `services/api-gateway/`: cổng vào thống nhất cho frontend và client.
- `services/auth-service/`: auth demo với CAPTCHA và login.
- `services/account-service/`: quản lý identity, user nội bộ và phân quyền.
- `services/catalog-service/`: quản lý sản phẩm, nhà cung cấp và offer.
- `services/livestream-service/`: quản lý nền tảng, phòng livestream và gán sản phẩm cho room.
- `services/ai-service/`: phân tích comment và cân bằng viewer.
- `services/sync-service/`: nhận comment qua API, gọi `ai-service` để enrich và lưu lịch sử sync trong memory.
- `services/report-service/`: tổng hợp KPI bằng cách gọi `identity`, `catalog`, `livestream` và `sync`.

## Chạy backend bằng Docker

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
- `http://localhost:8006`: Catalog Service
- `http://localhost:8007`: Livestream Service

Các URL nên dùng để kiểm tra:

- API Gateway:
  - root: `http://localhost:8000/`
  - health: `http://localhost:8000/health`
  - docs: `http://localhost:8000/docs`
- AI Service:
  - root: `http://localhost:8001/`
  - health: `http://localhost:8001/health`
  - docs: `http://localhost:8001/docs`
- Auth Service:
  - root: `http://localhost:8002/`
  - health: `http://localhost:8002/health`
  - docs: `http://localhost:8002/docs`
- Account Service:
  - root: `http://localhost:8003/`
  - health: `http://localhost:8003/health`
  - docs: `http://localhost:8003/docs`
- Sync Service:
  - root: `http://localhost:8004/`
  - health: `http://localhost:8004/health`
  - docs: `http://localhost:8004/docs`
- Report Service:
  - root: `http://localhost:8005/`
  - health: `http://localhost:8005/health`
  - docs: `http://localhost:8005/docs`
- Catalog Service:
  - root: `http://localhost:8006/`
  - health: `http://localhost:8006/health`
  - docs: `http://localhost:8006/docs`
- Livestream Service:
  - root: `http://localhost:8007/`
  - health: `http://localhost:8007/health`
  - docs: `http://localhost:8007/docs`

Lưu ý:

- Nếu bạn đang chạy image cũ thì root `/` có thể vẫn báo `Not Found`.
- Khi đó cần build lại:

```bash
cd backend
docker compose up --build
```

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

- `account-service`, `catalog-service`, `livestream-service` đang dùng chung dữ liệu seed và SQLite trong `services/account-service/app/data/`, được chia theo từng domain như `identity/`, `catalog/`, `livestream/`, `sqlite/`.
- `sync-service` hiện chưa có database riêng.
- `report-service` chỉ tổng hợp từ API nội bộ của các service khác.
