# Báo Cáo Project

## Smart Livestream Management Platform

## 1. Giới thiệu

`Smart Livestream Management Platform` là project xây dựng một nền tảng hỗ trợ quản lý và vận hành hoạt động livestream bán hàng theo hướng `Service-Oriented Architecture (SOA)` và triển khai bằng các service độc lập. Hệ thống tập trung giải quyết các bài toán thực tế như quản lý tài khoản live, quản lý nhân sự, quản lý sản phẩm, hỗ trợ bán hàng trong phiên live, phân tích bình luận bằng AI và tổng hợp báo cáo vận hành.

Project gồm hai ứng dụng giao diện:

- `frontend/`: dashboard quản lý dành cho admin, nhân viên bán hàng và quản lý sản phẩm.
- `apps/demo-app/`: ứng dụng mô phỏng phiên livestream, khách hàng, giỏ hàng, bình luận và hội thoại trong lúc live.

Phần backend được tách thành nhiều microservice `FastAPI`, giao tiếp thông qua `API Gateway`.

## 2. Mục tiêu của project

Project được xây dựng với các mục tiêu chính:

- Mô phỏng mô hình hệ thống livestream bán hàng theo kiến trúc dịch vụ.
- Tách biệt các nghiệp vụ chính thành các service độc lập để dễ mở rộng và bảo trì.
- Đồng bộ dữ liệu dùng chung giữa các ứng dụng quản lý và ứng dụng demo.
- Ứng dụng AI để phân tích mức độ quan tâm của khách hàng thông qua bình luận trong phiên live.
- Hỗ trợ theo dõi hoạt động vận hành và tổng hợp chỉ số báo cáo.

## 3. Phạm vi chức năng

Ở phiên bản hiện tại, hệ thống hỗ trợ các nhóm chức năng sau:

- Quản lý tài khoản nội bộ với các vai trò `admin`, `staff`, `product_manager`.
- Quản lý khách hàng, đăng ký tài khoản khách hàng theo số điện thoại.
- Quản lý danh mục sản phẩm, nhà cung cấp và offer nhập hàng.
- Gán sản phẩm cho từng phòng livestream trước khi bán.
- Ghim sản phẩm đang bán trong phiên live với giá live riêng.
- Hỗ trợ khách hàng thêm sản phẩm vào giỏ hàng, xóa giỏ hàng, checkout và lưu đơn hàng.
- Ghi nhận bình luận trong phiên livestream.
- AI chủ động mở hội thoại với khách hàng khi phát hiện bình luận có tín hiệu quan tâm.
- Nhân viên bán hàng tiếp tục trả lời khách hàng trong hội thoại sau khi AI mở đầu.
- Tổng hợp KPI và dữ liệu vận hành từ nhiều service.

## 4. Kiến trúc hệ thống

Hệ thống được tổ chức theo mô hình nhiều service độc lập:

- `api-gateway`: cổng vào thống nhất cho frontend và demo app.
- `auth-service`: xử lý CAPTCHA và đăng nhập.
- `account-service`: quản lý người dùng nội bộ, khách hàng, giỏ hàng, đơn hàng, bình luận và hội thoại.
- `catalog-service`: quản lý sản phẩm, nhà cung cấp và bảng giá nhà cung cấp.
- `livestream-service`: quản lý nền tảng, phòng livestream, gán sản phẩm và live offer.
- `ai-service`: phân tích bình luận và hỗ trợ cân bằng viewer.
- `sync-service`: đồng bộ comment và làm giàu dữ liệu qua AI.
- `report-service`: tổng hợp dữ liệu và KPI từ các service khác.

Ba service `account-service`, `catalog-service` và `livestream-service` đang dùng chung dữ liệu trên `SQLite`, kết hợp với các file JSON seed để khởi tạo dữ liệu mẫu. Kiến trúc này phù hợp với mục tiêu học tập và mô phỏng, đồng thời vẫn thể hiện được cách tổ chức hệ thống theo hướng SOA/microservices.

## 5. Công nghệ sử dụng

- Backend: `Python`, `FastAPI`
- Frontend: `HTML`, `CSS`, `JavaScript`
- Cơ sở dữ liệu: `SQLite`
- AI/ML: `scikit-learn`
- Đóng gói và triển khai: `Docker`, `Docker Compose`

## 6. Luồng nghiệp vụ chính

### 6.1. Quản lý và bán hàng trong phiên livestream

1. Quản lý sản phẩm tạo và cập nhật sản phẩm trong hệ thống.
2. Sản phẩm được gán cho từng phòng livestream trước khi lên live.
3. Nhân viên bán hàng chọn sản phẩm đã được gán và ghim lên phiên live với giá giảm riêng.
4. Khách hàng xem sản phẩm, thêm vào giỏ hàng và thực hiện mua hàng.
5. Đơn hàng và tồn kho được lưu đồng bộ vào database dùng chung.

### 6.2. Tương tác khách hàng và hỗ trợ bằng AI

1. Khách hàng để lại bình luận trong phiên livestream.
2. `account-service` gửi nội dung bình luận sang `ai-service` để phân tích.
3. Nếu AI phát hiện tín hiệu quan tâm, hệ thống tự động mở hội thoại với khách hàng.
4. Nhân viên bán hàng tiếp tục trả lời trong cùng hội thoại để tư vấn và chốt đơn.

### 6.3. Báo cáo và giám sát

1. `report-service` gọi dữ liệu từ `account-service`, `catalog-service`, `livestream-service` và `sync-service`.
2. Hệ thống tổng hợp các chỉ số như số tài khoản live, số sản phẩm, số khách hàng, số comment đồng bộ và KPI vận hành.

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

Chạy riêng ứng dụng demo:

```bash
cd apps/demo-app
python -m http.server 3010
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

- Admin: `admin@smartlive.vn` / `123456`
- Nhân viên bán hàng: `staff@smartlive.vn` / `staff01`
- Quản lý sản phẩm: `product.manager@smartlive.vn` / `pm001`

## 10. Kết quả đạt được

Sau quá trình xây dựng và hoàn thiện, project đã đạt được một số kết quả chính:

- Xây dựng được mô hình hệ thống chia service theo nghiệp vụ rõ ràng.
- Đồng bộ dữ liệu chính giữa các app thông qua backend và database dùng chung.
- Mô phỏng được luồng bán hàng cơ bản trong livestream: gán sản phẩm, ghim sản phẩm, thêm giỏ hàng, mua hàng.
- Mô phỏng được luồng AI hỗ trợ bán hàng thông qua phân tích bình luận và mở hội thoại với khách hàng.
- Cung cấp được dashboard quản trị và demo app để kiểm thử nhiều vai trò sử dụng.

## 11. Hạn chế hiện tại

Project vẫn còn một số giới hạn:

- Dữ liệu thời gian thực hiện vẫn chủ yếu theo hướng đồng bộ API, chưa hoàn chỉnh theo mô hình realtime đầy đủ như WebSocket.
- Hệ thống hiện phù hợp cho mục tiêu học tập, mô phỏng nghiệp vụ và demo kiến trúc hơn là triển khai production.
- Một số thành phần AI hiện đang ở mức mô phỏng và fallback rule-based khi chưa có model phù hợp.

## 12. Hướng phát triển

Trong các bước tiếp theo, hệ thống có thể được mở rộng theo các hướng:

- Bổ sung đồng bộ realtime giữa các ứng dụng bằng WebSocket hoặc message broker.
- Hoàn thiện cơ chế theo dõi viewer và trạng thái live theo thời gian thực.
- Nâng cấp AI theo hướng gợi ý phản hồi tốt hơn và hỗ trợ chốt đơn thông minh hơn.
- Tách cơ sở dữ liệu theo từng service đúng hơn với kiến trúc microservices production.
- Bổ sung logging, monitoring và bảo mật ở mức triển khai thực tế.

## 13. Kết luận

Project `Smart Livestream Management Platform` đã thể hiện được ý tưởng xây dựng một nền tảng quản lý livestream bán hàng theo kiến trúc hướng dịch vụ, trong đó mỗi service đảm nhiệm một vai trò riêng nhưng vẫn liên kết thành một hệ thống thống nhất. Dù còn ở mức mô phỏng và học thuật, project đã bao quát được nhiều thành phần quan trọng của một hệ thống thực tế như quản lý tài khoản, quản lý sản phẩm, xử lý tương tác khách hàng, hỗ trợ AI và báo cáo vận hành.
