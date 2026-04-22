# Báo cáo Project

## Smart Livestream Management Platform

## 1. Giới thiệu

`Smart Livestream Management Platform` là đồ án xây dựng hệ thống hỗ trợ quản lý và vận hành hoạt động livestream bán hàng theo kiến trúc hướng dịch vụ. Hệ thống được tách thành nhiều service độc lập để mô phỏng cách tổ chức một nền tảng livestream có nhiều vai trò sử dụng, nhiều nguồn dữ liệu và nhiều luồng nghiệp vụ chạy đồng thời.

Project hiện có 2 ứng dụng giao diện chính:

- `frontend/`: app quản lý dành cho `admin` và `quản lý sản phẩm`
- `apps/demo-app/`: app livestream demo dành cho `nhân viên bán hàng` và `khách hàng`

Hai ứng dụng này cùng dùng dữ liệu thật từ backend thông qua `api-gateway`. Những thành phần như phòng live, sản phẩm, phân công sản phẩm, bình luận, hội thoại, giỏ hàng, đơn hàng và cấu hình AI đều được đồng bộ qua backend thay vì lưu tách rời ở frontend.

## 2. Mục tiêu của đề tài

- Áp dụng kiến trúc `Service-Oriented Architecture` vào bài toán livestream bán hàng
- Tách nghiệp vụ thành các service độc lập để dễ mở rộng và bảo trì
- Xây dựng luồng quản lý phòng live, sản phẩm, khách hàng và đơn hàng trên dữ liệu dùng chung
- Mô phỏng tương tác giữa nhân viên bán hàng và khách hàng trong phiên live
- Tích hợp AI để phát hiện khách quan tâm và chủ động mở đầu hội thoại
- Cung cấp dashboard quản lý phục vụ theo dõi hoạt động hệ thống

## 3. Phạm vi chức năng hiện tại

### 3.1. App quản lý

- `Admin` đăng nhập để quản trị hệ thống
- `Quản lý sản phẩm` đăng nhập để thao tác danh mục
- Quản lý phòng livestream và tài khoản nhân viên bán hàng
- Thêm, xem và xóa tài khoản nhân viên bán hàng
- Quản lý sản phẩm, nhà cung cấp, offer và cấu hình gán sản phẩm cho từng phòng live
- Cấu hình trợ lý AI: bật hoặc tắt AI, sửa mẫu tin nhắn AI gửi cho khách hàng

### 3.2. App demo livestream

- `Nhân viên bán hàng` đăng nhập bằng tài khoản do admin cấp
- `Khách hàng` có thể đăng ký tài khoản mới hoặc đăng nhập bằng số điện thoại / email
- Khách hàng chọn phòng live, xem nội dung live, bình luận, nhắn tin với shop, thêm vào giỏ hàng và mua hàng
- Nhân viên bán hàng có thể cấp quyền camera, bắt đầu live, ghim sản phẩm và đặt giá live trước khi ghim
- AI có thể tự mở đầu hội thoại khi phát hiện khách để lại bình luận thể hiện ý định mua
- Nhân viên bán hàng tiếp tục trả lời trong cùng luồng hội thoại

### 3.3. Đồng bộ dữ liệu

- `frontend` và `demo-app` cùng đọc và ghi dữ liệu qua backend
- Số viewer được tính theo cơ chế presence/heartbeat, không dùng số giả cố định
- Bình luận, hội thoại, giỏ hàng, đơn hàng và live offer đều lưu trong database dùng chung

## 4. Kiến trúc hệ thống

Hệ thống gồm các service chính:

- `api-gateway`: cổng vào thống nhất cho các ứng dụng frontend
- `auth-service`: xử lý CAPTCHA và đăng nhập
- `account-service`: quản lý user nội bộ, khách hàng, giỏ hàng, đơn hàng, bình luận, hội thoại và cấu hình AI
- `catalog-service`: quản lý sản phẩm, nhà cung cấp và supplier offers
- `livestream-service`: quản lý phòng livestream, phân công sản phẩm, live offer, trạng thái live và presence viewer
- `ai-service`: phân tích bình luận và hỗ trợ nhận diện khách hàng quan tâm
- `sync-service`: đồng bộ dữ liệu comment mẫu và enrich dữ liệu với AI
- `report-service`: tổng hợp dữ liệu và KPI từ các service khác

## 5. Công nghệ sử dụng

- Backend: `Python`, `FastAPI`
- Frontend: `HTML`, `CSS`, `JavaScript`
- Cơ sở dữ liệu: `SQLite`
- AI/ML: `scikit-learn`, `joblib`
- Triển khai: `Docker`, `Docker Compose`

## 6. Luồng nghiệp vụ chính

### 6.1. Luồng quản lý sản phẩm và phòng live

1. `Admin` hoặc `quản lý sản phẩm` tạo sản phẩm trong hệ thống
2. Sản phẩm được gán vào phòng livestream trước phiên bán
3. Nhân viên bán hàng chỉ nhìn thấy các sản phẩm đã được cấp cho phòng mình phụ trách
4. Khi lên live, nhân viên chọn giá live giảm rồi ghim sản phẩm lên phiên live

### 6.2. Luồng khách hàng mua hàng

1. Khách hàng đăng ký hoặc đăng nhập vào demo app
2. Khách chọn phòng live đang quan tâm
3. Khách xem sản phẩm ghim, bình luận hỏi hàng, thêm sản phẩm vào giỏ hàng
4. Khi checkout, đơn hàng được lưu xuống backend và tồn kho được cập nhật theo dữ liệu thật

### 6.3. Luồng AI hỗ trợ hội thoại

1. Khách hàng để lại bình luận trong phòng live
2. Bình luận được gửi tới backend và phân tích qua `ai-service`
3. Nếu bình luận thể hiện nhu cầu mua hàng, AI tự gửi tin nhắn mở đầu hội thoại
4. Nhân viên bán hàng tiếp quản phần trả lời để tư vấn và chốt đơn

### 6.4. Luồng đồng bộ giữa hai app

- App quản lý và app demo dùng chung dữ liệu qua `api-gateway`
- Thông tin phòng live, sản phẩm, gán sản phẩm, live offer, viewer, comment và message đều lấy từ backend
- Số viewer phản ánh client thật đang mở room thông qua heartbeat/presence

## 7. Cấu trúc thư mục chính

```text
frontend/                 App quản lý
apps/
  demo-app/               App livestream demo
backend/
  services/               Các microservice FastAPI
  README.md
infra/docker/             Docker Compose chạy toàn hệ thống
ml/                       Dữ liệu và script huấn luyện model
docs/                     Tài liệu kiến trúc
```

## 8. Cách chạy hệ thống

Chạy toàn bộ hệ thống:

```bash
cd infra/docker
docker compose up --build
```

Địa chỉ mặc định:

- App quản lý: `http://localhost:3000`
- App demo livestream: `http://localhost:3010`
- API Gateway: `http://localhost:8000`

## 9. Tài khoản mẫu

### 9.1. App quản lý

- `admin@smartlive.vn / 123456`
- `product.manager@smartlive.vn / pm001`

Lưu ý:
- App quản lý yêu cầu nhập đúng CAPTCHA khi đăng nhập

### 9.2. App demo livestream

- Nhân viên bán hàng: `staff@smartlive.vn / staff01`
- Khách hàng demo 1: `0901234567 / 123456`
- Khách hàng demo 2: `0912345678 / 123456`

Ngoài ra khách hàng có thể tự đăng ký tài khoản mới ngay trong demo app.

## 10. Kết quả đạt được

- Xây dựng được hệ thống chia service theo nghiệp vụ rõ ràng
- Đồng bộ dữ liệu dùng chung giữa app quản lý và app demo
- Mô phỏng được luồng bán hàng cơ bản trong livestream
- Mô phỏng được luồng AI mở đầu hội thoại với khách hàng quan tâm
- Có dashboard quản lý để theo dõi tài khoản, phòng live, sản phẩm và cấu hình AI

## 11. Hạn chế hiện tại

- Dữ liệu realtime hiện dùng heartbeat/polling, chưa phải WebSocket production hoàn chỉnh
- Một số phần giao diện vẫn còn cần chuẩn hóa thêm về tiếng Việt và hiển thị
- AI hiện mới tập trung vào phân tích bình luận và mở đầu hội thoại, chưa tự động trả lời thay nhân viên

## 12. Hướng phát triển

- Bổ sung WebSocket hoặc message broker cho realtime tốt hơn
- Hoàn thiện dashboard theo dõi viewer và trạng thái live theo thời gian thực
- Mở rộng khả năng AI trong hỗ trợ tư vấn và gợi ý sản phẩm
- Tách database rõ ràng hơn cho từng service theo mô hình production
- Bổ sung logging, monitoring và kiểm soát quyền truy cập chi tiết hơn

## 13. Kết luận

Project đã mô phỏng được một nền tảng quản lý livestream bán hàng theo kiến trúc hướng dịch vụ với nhiều vai trò sử dụng và nhiều luồng nghiệp vụ liên kết với nhau. Dù vẫn ở mức đồ án và demo học thuật, hệ thống hiện đã thể hiện rõ cách tách service, cách đồng bộ dữ liệu giữa nhiều ứng dụng và cách tích hợp AI vào quy trình hỗ trợ bán hàng trong phiên livestream.
