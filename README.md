# Smart Livestream Management Platform

## 1. Giới thiệu đề tài

Đây là đề tài xây dựng một ứng dụng quản lý đa tài khoản livestream theo hướng kiến trúc dịch vụ, có tích hợp AI để đánh giá bình luận, nhận diện khách hàng tiềm năng, cân bằng người xem để giảm lag và triển khai trên nền tảng đám mây.

Hệ thống hướng đến các shop online, đội ngũ bán hàng hoặc doanh nghiệp đang vận hành livestream trên nhiều kênh cùng lúc. Thay vì phải theo dõi từng tài khoản riêng lẻ, người dùng có thể quản lý tập trung, đồng bộ dữ liệu bình luận, phân loại mức độ quan tâm của khách hàng, ưu tiên chăm sóc những lead có khả năng chuyển đổi cao và điều hướng viewer đến những tài khoản ổn định hơn khi lưu lượng truy cập tăng mạnh.

## 2. Mục tiêu

- Quản lý tập trung nhiều tài khoản livestream.
- Hỗ trợ mỗi nền tảng có nhiều tài khoản livestream độc lập.
- Đồng bộ comment từ nhiều nguồn về một hệ thống duy nhất.
- Ứng dụng AI để phân tích comment theo cảm xúc, ý định và mức độ tiềm năng.
- Có thể train model thật cho intent và sentiment từ dữ liệu gán nhãn.
- Ứng dụng AI để cân bằng viewer giữa các tài khoản livestream nhằm giảm lag.
- Triển khai hệ thống trên cloud theo hướng có thể mở rộng.
- Hỗ trợ dashboard theo dõi hiệu quả livestream và hành vi khách hàng.

## 3. Bài toán thực tế

Trong quá trình livestream bán hàng, người vận hành thường gặp các vấn đề:

- Comment đến quá nhanh, khó theo dõi bằng tay.
- Có nhiều kênh livestream khác nhau cần quản lý đồng thời.
- Mỗi kênh có thể có nhiều tài khoản livestream, gây khó khăn trong quản lý nếu không có dashboard tập trung.
- Khó phân biệt comment nào là khách thật sự quan tâm.
- Không có cơ chế chấm điểm lead để ưu tiên tư vấn.
- Một số tài khoản bị quá tải viewer dẫn đến lag, trong khi tài khoản khác vẫn còn dư tài nguyên.
- Dữ liệu phân tán, khó tổng hợp để đánh giá hiệu quả.

## 4. Chức năng chính

- Đăng nhập, phân quyền người dùng.
- Quản lý nhiều tài khoản livestream theo từng nền tảng.
- Thêm mới nhiều tài khoản trong cùng một nền tảng.
- Đồng bộ comment từ nhiều kênh.
- Gom nhóm và hiển thị comment theo livestream hoặc theo tài khoản.
- AI phân tích comment: sentiment, intent, lead score.
- Train model comment AI bằng dữ liệu gán nhãn.
- AI cân bằng viewer giữa các tài khoản để chống lag.
- Lọc comment quan trọng.
- Gợi ý phản hồi nhanh.
- Dashboard thống kê và báo cáo.
- Lưu trữ lịch sử dữ liệu trên cloud.

## 5. Kiến trúc tổng quan

Hệ thống được xây dựng theo hướng service-oriented architecture kết hợp cloud-native. Trong phạm vi repo hiện tại, các thành phần chính gồm:

- Frontend Dashboard
- API Gateway
- Auth Service
- Account Service
- Livestream Sync Service
- AI Service cho comment analysis và viewer balancing
- Reporting Service
- SQLite cho dữ liệu quản trị
- ML models cho intent và sentiment
- Docker Compose để chạy toàn hệ thống

Về mặt ý tưởng phát triển tiếp, hệ thống có thể mở rộng thêm:

- Lead Scoring Service tách riêng
- Notification Service
- PostgreSQL
- Redis hoặc message queue
- Object Storage

## 6. Thành phần AI

AI được sử dụng để đánh giá comment theo các tiêu chí:

- Cảm xúc: tích cực, trung tính, tiêu cực.
- Ý định: hỏi giá, muốn mua, cần tư vấn, spam.
- Mức độ tiềm năng: từ 0 đến 100.
- Mức ưu tiên xử lý: cao, trung bình, thấp.
- Cân bằng lượng viewer giữa các tài khoản livestream để giảm nguy cơ lag.
- Đề xuất kênh ưu tiên nhận viewer mới khi lưu lượng truy cập tăng đột biến.

Trong repo hiện tại, `ai-service` đã triển khai:

- `POST /analyze-comment`
- `POST /analyze-comments/batch`
- `POST /balance-viewers`
- `POST /session-optimizer`

Model có thể được train lại từ dữ liệu trong `ml/data/comments_labeled.csv` và load từ `ml/models/`.

## 7. Báo cáo và dashboard

Hệ thống không chỉ quản lý dữ liệu mà còn hỗ trợ theo dõi báo cáo vận hành. Trong repo hiện tại, `report-service` đã tổng hợp được các báo cáo sau:

### Báo cáo KPI tổng quan

API:

- `GET /api/v1/reports/kpis/overview`

Nội dung báo cáo gồm:

- Tổng số nền tảng đang quản lý.
- Tổng số tài khoản livestream.
- Tổng số sản phẩm.
- Tổng số nhà cung cấp.
- Số offer đang active.
- Nền tảng có lượng viewer nổi bật nhất.
- Tổng số sync job.
- Tổng số comment đã đồng bộ.
- Tổng số comment ưu tiên cao.

### Báo cáo vận hành

API:

- `GET /api/v1/reports/operations`

Nội dung báo cáo gồm:

- Thời điểm tạo báo cáo.
- KPI tổng quan toàn hệ thống.
- Thống kê comment theo từng nền tảng.
- Số comment ưu tiên cao theo từng nền tảng.
- Điểm lead trung bình theo từng nền tảng.
- Danh sách các sync job gần nhất.

### Dashboard frontend

Frontend hiện hiển thị được:

- Thông tin đăng nhập và vai trò người dùng.
- KPI tổng quan cho admin.
- Danh sách tài khoản livestream theo nền tảng.
- Danh mục sản phẩm.
- Nhà cung cấp và supplier offers.
- Kết quả phân tích comment bằng AI.
- Gợi ý cân bằng viewer giữa các room livestream.

## 8. Tích hợp cloud

Hệ thống được định hướng triển khai trên nền tảng cloud cho môn học. Trong repo hiện tại:

- `infra/docker/docker-compose.yml` dùng để chạy nhanh toàn bộ stack.
- `backend/docker-compose.yml` dùng để chạy riêng backend.
- `docs/cloud-deployment.md` mô tả định hướng triển khai cloud.

Hiện tại repo mới tập trung vào demo kiến trúc dịch vụ và luồng API nội bộ. Các thành phần như managed database, queue và object storage vẫn là hướng mở rộng tiếp theo.

## 9. Roadmap phát triển

### Giai đoạn 1 - MVP

- Đăng nhập và phân quyền.
- Quản lý nhiều tài khoản livestream theo nền tảng.
- Thêm mới tài khoản trên cùng một nền tảng.
- Đồng bộ comment giả lập hoặc từ một nền tảng.
- AI phân loại comment cơ bản.
- Train model intent và sentiment từ dữ liệu mẫu.
- AI viewer balancing để chống lag.
- Dashboard lead tiềm năng.

### Giai đoạn phát triển tiếp theo

- Kết nối API thật với nền tảng livestream.
- Tách lead scoring thành service riêng.
- Bổ sung notification service.
- Lưu lịch sử sync vào database thay vì memory.
- Tích hợp message queue để xử lý gần realtime hơn.
- Mở rộng báo cáo và lưu trữ dữ liệu dài hạn.

## 10. Hướng phát triển khả thi trong repo

- `frontend/`: dashboard gọi API và hiển thị kết quả AI.
- `backend/services/api-gateway/`: đầu vào thống nhất cho frontend.
- `backend/services/auth-service/`: đăng nhập và thông tin người dùng.
- `backend/services/account-service/`: quản lý nhiều tài khoản livestream, sản phẩm, nhà cung cấp và offer bằng SQLite.
- `backend/services/sync-service/`: đồng bộ comment và sự kiện livestream qua API.
- `backend/services/ai-service/`: phân tích comment và cân bằng viewer để chống lag.
- `backend/services/report-service/`: dashboard và tổng hợp KPI.
- `ml/`: dữ liệu gán nhãn, script train và model đã train.
- `infra/`: Docker Compose và tài liệu hạ tầng.
- `docs/`: tài liệu kiến trúc, use case, roadmap, deployment.

## 11. Mã nguồn đã có trong repo

- `frontend/`: static dashboard trên trình duyệt.
- `backend/services/api-gateway/`: FastAPI gateway gom API cho frontend.
- `backend/services/auth-service/`: FastAPI service cho đăng nhập và CAPTCHA.
- `backend/services/account-service/`: FastAPI service dùng SQLite để quản lý người dùng, tài khoản livestream, mặt hàng, nhà cung cấp và offer.
- `backend/services/ai-service/`: FastAPI service cho phân tích comment và viewer balancing.
- `backend/services/sync-service/`: FastAPI service nhận comment đồng bộ và gọi `ai-service` để enrich dữ liệu.
- `backend/services/report-service/`: FastAPI service tổng hợp KPI và báo cáo vận hành.
- `ml/`: pipeline train `intent` và `sentiment` bằng scikit-learn.
- `infra/docker/docker-compose.yml`: chạy nhanh toàn bộ stack bằng Docker Compose.
- `backend/docker-compose.yml`: chạy nhanh riêng phần backend.

## 12. Hướng dẫn chạy dự án

### Cách 1 - Chạy nhanh bằng Docker Compose

Đây là cách phù hợp nhất để chạy nhanh toàn bộ hệ thống.

```bash
cd infra/docker
docker compose up --build
```

Sau khi chạy xong, các service mặc định sẽ mở trên:

- Frontend: `http://localhost:3000`
- API Gateway: `http://localhost:8000`
- AI Service: `http://localhost:8001`
- Auth Service: `http://localhost:8002`
- Account Service: `http://localhost:8003`
- Sync Service: `http://localhost:8004`
- Report Service: `http://localhost:8005`

Để dừng hệ thống:

```bash
cd infra/docker
docker compose down
```

### Cách 2 - Chạy riêng backend

```bash
cd backend
docker compose up --build
```

## 13. Tài khoản hệ thống

Bạn có thể đăng nhập bằng tài khoản mẫu:

- Admin: `admin@smartlive.vn` - Mật khẩu: `123456`
- Nhân viên: `staff@smartlive.vn` - Mật khẩu: `staff01`
- Nhân viên 02: `staff02@smartlive.vn` - Mật khẩu: `staff02`
- Nhân viên 03: `staff03@smartlive.vn` - Mật khẩu: `staff03`
- Nhân viên 04: `staff04@smartlive.vn` - Mật khẩu: `staff04`

Lưu ý:

- Frontend đăng nhập qua CAPTCHA từ `auth-service`.
- `auth-service` hiện là demo service, chưa dùng database riêng.

## 14. Database seed và dữ liệu mẫu

`account-service` sẽ tự tạo SQLite database khi khởi động tại:

- `backend/services/account-service/app/data/account_management.db`

Dữ liệu mẫu hiện có gồm:

- user admin và nhiều user staff,
- tài khoản livestream TikTok,
- tài khoản livestream Facebook,
- sản phẩm,
- nhà cung cấp,
- supplier offers.

Ngoài SQLite, repo còn có dữ liệu JSON seed trong:

- `backend/services/account-service/app/data/`

## 15. API hiện có qua gateway

### Health check

- `GET /health`

### Auth

- `GET /api/v1/auth/captcha`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### Account data

- `GET /api/v1/users`
- `GET /api/v1/livestream-accounts`
- `GET /api/v1/livestream-accounts/grouped`
- `GET /api/v1/platform-summaries`
- `GET /api/v1/platforms/{platform}/accounts`
- `POST /api/v1/livestream-accounts`
- `GET /api/v1/products`
- `GET /api/v1/suppliers`
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

## 16. Ví dụ gọi API

### Kiểm tra health gateway

```bash
curl http://localhost:8000/health
```

### Lấy CAPTCHA

```bash
curl http://localhost:8000/api/v1/auth/captcha
```

### Lấy danh sách tài khoản livestream

```bash
curl http://localhost:8000/api/v1/livestream-accounts
```

### Đồng bộ một comment qua sync-service

```bash
curl -X POST http://localhost:8000/api/v1/sync/comments \
  -H "Content-Type: application/json" \
  -d '{
    "comment": "shop oi mau nay con hang khong",
    "username": "khach_a",
    "livestream_id": "live-tiktok-01",
    "account_id": "ls-tiktok-01",
    "platform": "tiktok",
    "source": "tiktok-comments",
    "source_comment_id": "cmt-1001"
  }'
```

### Lấy báo cáo KPI tổng quan

```bash
curl http://localhost:8000/api/v1/reports/kpis/overview
```

### Lấy báo cáo vận hành

```bash
curl http://localhost:8000/api/v1/reports/operations
```

## 17. Train AI comment

```bash
pip install -r backend/services/ai-service/requirements.txt
python ml/training/train_comment_models.py
```

Sau khi train xong, service sẽ tự động load model từ:

- `ml/models/intent_model.joblib`
- `ml/models/sentiment_model.joblib`

Nếu chưa có model, `ai-service` sẽ fallback về rule-based analyzer.

## 18. Kiểm thử hiện có

Repo hiện có test logic cho `ai-service` tại:

- `backend/services/ai-service/tests/test_ai_logic.py`

## 19. Gợi ý đọc tiếp

- [Tài liệu backend](backend/README.md)
- [Kiến trúc hệ thống](docs/architecture.md)
- [AI analysis](docs/ai-analysis.md)
- [Use cases](docs/use-cases.md)
- [Cloud deployment](docs/cloud-deployment.md)
