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

Hệ thống được đề xuất theo hướng service-oriented architecture kết hợp cloud-native:

- Frontend Dashboard
- API Gateway
- Auth Service
- Account Service
- Livestream Sync Service
- Comment Analysis Service
- Lead Scoring Service
- Viewer Balancing AI Module
- Notification Service
- Reporting Service
- PostgreSQL
- Redis
- Object Storage

## 6. Thành phần AI

AI được sử dụng để đánh giá comment theo các tiêu chí:

- Cảm xúc: tích cực, trung tính, tiêu cực.
- Ý định: hỏi giá, muốn mua, cần tư vấn, spam.
- Mức độ tiềm năng: từ 0 đến 100.
- Mức ưu tiên xử lý: cao, trung bình, thấp.
- Cân bằng lượng viewer giữa các tài khoản livestream để giảm nguy cơ lag.
- Đề xuất kênh ưu tiên nhận viewer mới khi lưu lượng truy cập tăng đột biến.

## 7. Tích hợp cloud

Hệ thống triển khai trên nền tảng Databricks theo định hướng cloud cho môn học, kết hợp các thành phần xử lý dữ liệu, notebook, jobs và giám sát tiến độ triển khai.

## 8. Roadmap phát triển

### Giai đoạn 1 - MVP

- Đăng nhập và phân quyền.
- Quản lý nhiều tài khoản livestream theo nền tảng.
- Thêm mới tài khoản trên cùng một nền tảng.
- Đồng bộ comment giả lập hoặc từ một nền tảng.
- AI phân loại comment cơ bản.
- Train model intent/sentiment từ dữ liệu mẫu.
- AI viewer balancing để chống lag.
- Dashboard lead tiềm năng.

## 9. Hướng phát triển khả thi trong repo

- `frontend/`: dashboard demo gọi API và hiển thị kết quả AI.
- `services/api-gateway/`: đầu vào thống nhất cho frontend.
- `services/auth-service/`: đăng nhập demo và thông tin người dùng.
- `services/account-service/`: quản lý nhiều tài khoản livestream theo từng nền tảng.
- `services/sync-service/`: đồng bộ comment và sự kiện livestream.
- `services/ai-service/`: phân tích comment và cân bằng viewer để chống lag.
- `ml/`: dữ liệu gán nhãn, script train và model đã train.
- `services/report-service/`: dashboard và tổng hợp KPI.
- `infra/`: Docker Compose, Kubernetes manifest, Terraform.
- `docs/`: tài liệu kiến trúc, use case, sequence, roadmap, deployment.

## 10. Mã nguồn đã có trong repo

- `frontend/`: static dashboard cho demo trên trình duyệt.
- `services/ai-service/`: FastAPI service cho phân tích comment và viewer balancing.
- `services/auth-service/`: FastAPI service cho đăng nhập demo.
- `services/account-service/`: FastAPI service cho dữ liệu tài khoản livestream, nhóm theo nền tảng và thống kê platform.
- `services/api-gateway/`: FastAPI gateway gom API cho frontend.
- `ml/`: pipeline train `intent` và `sentiment` bằng scikit-learn.
- `infra/docker/docker-compose.yml`: chạy nhanh toàn bộ stack bằng Docker Compose.

## 11. Hướng dẫn chạy dự án

### Cách 1 - Chạy nhanh bằng Docker Compose

Đây là cách phù hợp nhất để demo nhanh toàn bộ hệ thống.

Yêu cầu:

- Cài đặt Docker.
- Cài đặt Docker Compose.

Lệnh chạy:

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

Lưu ý:

- `0.0.0.0` chỉ là địa chỉ bind bên trong container hoặc server.
- Khi mở trên trình duyệt, hãy dùng `localhost` thay vì `0.0.0.0`.

Để dừng hệ thống:

```bash
cd infra/docker
docker compose down
```

### Tài khoản demo

Bạn có thể đăng nhập bằng tài khoản mẫu:

- Email: `admin@smartlive.vn` - Mật khẩu: `123456`
- Email: `staff@smartlive.vn` - Mật khẩu: `123456`

### Kiểm tra nhanh hệ thống

Có thể kiểm tra health check của gateway:

```bash
curl http://localhost:8000/health
```

Nếu hệ thống chạy đúng, gateway sẽ trả về trạng thái của `ai-service`, `auth-service` và `account-service`.

## 12. Train AI comment

```bash
pip install -r services/ai-service/requirements.txt
python ml/training/train_comment_models.py
```

Sau khi train xong, service sẽ tự động load model từ:

- `ml/models/intent_model.joblib`
- `ml/models/sentiment_model.joblib`

Nếu chưa có model, `ai-service` sẽ fallback về rule-based analyzer.
