# Backend

Thư mục này chứa toàn bộ backend của dự án.

## Cấu trúc

- `services/api-gateway/`: cổng vào API cho frontend
- `services/auth-service/`: xác thực người dùng demo
- `services/account-service/`: quản lý tài khoản livestream, sản phẩm, nhà cung cấp và offer
- `services/ai-service/`: phân tích comment và cân bằng viewer
- `services/sync-service/`: nơi dành cho luồng đồng bộ dữ liệu trong tương lai
- `services/report-service/`: nơi dành cho service báo cáo trong tương lai
- `docker-compose.yml`: chạy nhanh toàn bộ backend mà không cần frontend

## Chạy nhanh backend

```bash
cd backend
docker compose up --build
```

Sau khi chạy xong, các service backend sẽ mở trên:

- `http://localhost:8000`: API Gateway
- `http://localhost:8001`: AI Service
- `http://localhost:8002`: Auth Service
- `http://localhost:8003`: Account Service
