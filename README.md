# Báo Cáo Project

## Smart Livestream Management Platform

## 1. Giới thiệu

`Smart Livestream Management Platform` là project xây dựng nền tảng hỗ trợ quản lý và vận hành hoạt động livestream bán hàng theo hướng `Service-Oriented Architecture (SOA)`. Hệ thống tập trung vào các nghiệp vụ chính như quản lý tài khoản live, quản lý nhân sự, quản lý sản phẩm, hỗ trợ bán hàng trong phiên live, phân tích bình luận bằng AI và tổng hợp báo cáo vận hành.

Project gồm hai ứng dụng giao diện:

- `frontend/`: dashboard quản lý dành cho admin, nhân viên bán hàng và quản lý sản phẩm.
- `apps/demo-app/`: ứng dụng demo mô phỏng buổi livestream, khách hàng, giỏ hàng, bình luận và hội thoại trong lúc live.

Phần backend được tách thành nhiều microservice `FastAPI` và giao tiếp thông qua `API Gateway`.

## 2. Mục tiêu của project

- Mô phỏng hệ thống livestream bán hàng theo kiến trúc dịch vụ.
- Tách nghiệp vụ thành các service độc lập để dễ mở rộng và bảo trì.
- Đồng bộ dữ liệu dùng chung giữa app quản lý và app demo.
- Ứng dụng AI để nhận diện mức độ quan tâm của khách hàng trong phiên live.
- Hỗ trợ theo dõi hoạt động vận hành và tổng hợp KPI.

## 3. Phạm vi chức năng

- Quản lý tài khoản nội bộ với các vai trò `admin`, `staff`, `product_manager`.
- Quản lý khách hàng, đăng ký tài khoản khách hàng theo số điện thoại.
- Quản lý sản phẩm, nhà cung cấp và offer nhập hàng.
- Gán sản phẩm cho từng phòng livestream trước khi bán.
- Ghim sản phẩm trong phiên live với giá live riêng.
- Hỗ trợ giỏ hàng, checkout và lưu đơn hàng.
- Ghi nhận bình luận trong phiên livestream.
- AI chủ động mở đầu hội thoại khi phát hiện khách hàng quan tâm.
- Nhân viên tiếp tục trả lời khách trong cùng hội thoại.
- Tổng hợp báo cáo và KPI từ nhiều service.

## 4. Kiến trúc hệ thống

Hệ thống được chia thành các service chính:

- `api-gateway`: cổng vào thống nhất cho frontend và demo app.
- `auth-service`: xử lý CAPTCHA và đăng nhập.
- `account-service`: quản lý người dùng nội bộ, khách hàng, giỏ hàng, đơn hàng, bình luận và hội thoại.
- `catalog-service`: quản lý sản phẩm, nhà cung cấp và bảng giá nhà cung cấp.
- `livestream-service`: quản lý nền tảng, phòng livestream, gán sản phẩm, live offer và trạng thái live.
- `ai-service`: phân tích bình luận và hỗ trợ AI.
- `sync-service`: đồng bộ dữ liệu comment và enrich dữ liệu qua AI.
- `report-service`: tổng hợp dữ liệu và KPI từ các service khác.

Ba service `account-service`, `catalog-service` và `livestream-service` hiện dùng chung dữ liệu `SQLite` kết hợp với file JSON seed để phục vụ mục tiêu học tập và demo.

## 5. Công nghệ sử dụng

- Backend: `Python`, `FastAPI`
- Frontend: `HTML`, `CSS`, `JavaScript`
- Cơ sở dữ liệu: `SQLite`
- AI/ML: `scikit-learn`
- Triển khai: `Docker`, `Docker Compose`

## 6. Luồng nghiệp vụ chính

### 6.1. Luồng bán hàng trong phiên livestream

1. Quản lý sản phẩm tạo hoặc cập nhật sản phẩm trong hệ thống.
2. Sản phẩm được gán cho từng phòng livestream trước khi lên live.
3. Nhân viên bán hàng chọn sản phẩm đã được gán và ghim lên live với giá giảm riêng.
4. Khách hàng xem sản phẩm, thêm vào giỏ hàng và thực hiện mua hàng.
5. Đơn hàng và tồn kho được lưu đồng bộ vào database dùng chung.

### 6.2. Luồng AI hỗ trợ hội thoại

1. Khách hàng để lại bình luận trong phiên livestream.
2. `account-service` gửi nội dung bình luận sang `ai-service` để phân tích.
3. Nếu AI phát hiện tín hiệu quan tâm, hệ thống tự động mở hội thoại với khách hàng.
4. Nhân viên bán hàng tiếp tục trả lời để tư vấn và chốt đơn.

### 6.3. Luồng đồng bộ giữa 2 app

- `frontend` và `apps/demo-app` cùng đọc dữ liệu qua `api-gateway`.
- Trạng thái phiên live, viewer, bình luận, hội thoại, giỏ hàng và đơn hàng đều lấy từ backend.
- App demo dùng cơ chế presence/heartbeat để cập nhật số viewer thật theo client đang hoạt động.

## 7. Cấu trúc thư mục chính

```text
frontend/                               Dashboard quản lý chính
apps/
  demo-app/                             Ứng dụng demo livestream
backend/
  services/                             Các microservice FastAPI
  docker-compose.yml                    Chạy cụm backend
infra/docker/
  docker-compose.yml                    Chạy toàn bộ hệ thống
ml/                                     Dữ liệu huấn luyện và model AI
docs/                                   Tài liệu kiến trúc và mô tả hệ thống
```

## 8. Cách chạy hệ thống

Chạy toàn bộ hệ thống bằng Docker:

```bash
cd infra/docker
docker compose up --build
```

Các địa chỉ mặc định:

- Frontend dashboard: `http://localhost:3000`
- Demo app: `http://localhost:3010`
- API Gateway: `http://localhost:8000`
- AI Service: `http://localhost:8001`
- Auth Service: `http://localhost:8002`
- Account Service: `http://localhost:8003`
- Sync Service: `http://localhost:8004`
- Report Service: `http://localhost:8005`
- Catalog Service: `http://localhost:8006`
- Livestream Service: `http://localhost:8007`

## 9. Tài khoản mẫu

### Dashboard quản lý

- Admin: `admin@smartlive.vn` / `123456`
- Nhân viên bán hàng: `staff@smartlive.vn` / `staff01`
- Quản lý sản phẩm: `product.manager@smartlive.vn` / `pm001`

### Demo app livestream

- Nhân viên bán hàng: `staff@smartlive.vn` / `staff01`
- Khách hàng demo 1: `0901234567` / `123456`
- Khách hàng demo 2: `0912345678` / `123456`

## 10. Kết quả đạt được

- Xây dựng được hệ thống chia service theo nghiệp vụ rõ ràng.
- Đồng bộ dữ liệu chính giữa app quản lý và app demo thông qua backend.
- Mô phỏng được luồng bán hàng cơ bản trong livestream: gán sản phẩm, ghim sản phẩm, thêm giỏ hàng, mua hàng.
- Mô phỏng được luồng AI hỗ trợ bán hàng thông qua phân tích bình luận và mở hội thoại với khách hàng.
- Cung cấp dashboard quản trị và demo app để kiểm thử nhiều vai trò sử dụng.

## 11. Hạn chế hiện tại

- Dữ liệu realtime hiện vẫn chủ yếu theo cơ chế polling và heartbeat, chưa hoàn chỉnh như WebSocket production.
- Hệ thống phù hợp cho mục tiêu học tập và demo kiến trúc hơn là production.
- Một số thành phần AI vẫn ở mức mô phỏng hoặc fallback rule-based.

## 12. Hướng phát triển

- Bổ sung đồng bộ realtime đầy đủ bằng WebSocket hoặc message broker.
- Hoàn thiện theo dõi viewer và trạng thái live theo thời gian thực.
- Nâng cấp AI theo hướng hỗ trợ trả lời và chốt đơn thông minh hơn.
- Tách cơ sở dữ liệu riêng cho từng service đúng hơn với kiến trúc microservices production.
- Bổ sung logging, monitoring và cơ chế bảo mật đầy đủ hơn.

## 13. Kết luận

Project `Smart Livestream Management Platform` đã thể hiện được ý tưởng xây dựng một nền tảng quản lý livestream bán hàng theo kiến trúc hướng dịch vụ, trong đó mỗi service đảm nhiệm một vai trò riêng nhưng vẫn liên kết thành một hệ thống thống nhất. Dù còn ở mức mô phỏng và học thuật, project đã bao quát được nhiều thành phần quan trọng như quản lý tài khoản, quản lý sản phẩm, xử lý tương tác khách hàng, hỗ trợ AI và báo cáo vận hành.
