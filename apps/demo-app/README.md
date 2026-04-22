# Demo App

`apps/demo-app/` là ứng dụng mô phỏng phiên livestream bán hàng để trình bày luồng sử dụng thực tế giữa nhân viên bán hàng và khách hàng.

## 1. Mục đích

- Mô phỏng một phiên livestream mà không phụ thuộc trực tiếp vào nền tảng như TikTok Live hay Facebook Live
- Thể hiện rõ luồng xem live, bình luận, nhắn tin, ghim sản phẩm, thêm giỏ hàng và mua hàng
- Kiểm tra việc đồng bộ dữ liệu giữa app demo và app quản lý thông qua backend

## 2. Vai trò sử dụng

- `Nhân viên bán hàng`
- `Khách hàng`

App này không dùng cho `admin` hoặc `quản lý sản phẩm`.

## 3. Chức năng chính

### Nhân viên bán hàng

- Đăng nhập bằng tài khoản do admin cấp
- Cấp quyền camera và micro
- Bắt đầu hoặc kết thúc live
- Xem sản phẩm đã được gán cho phòng live
- Nhập giá live rồi ghim sản phẩm lên phiên live
- Theo dõi bình luận khách hàng
- Tiếp tục trả lời khách trong hội thoại do AI mở đầu

### Khách hàng

- Đăng ký tài khoản mới bằng số điện thoại
- Đăng nhập bằng số điện thoại hoặc email
- Chọn phòng live muốn xem
- Bình luận trong phiên live
- Nhắn tin với shop
- Thêm sản phẩm vào giỏ hàng
- Checkout và tạo đơn hàng

## 4. Đồng bộ dữ liệu

Demo app dùng dữ liệu thật qua backend:

- phòng livestream
- sản phẩm và live offer
- comment và message
- giỏ hàng và đơn hàng
- số viewer theo presence/heartbeat

Vì vậy khi dữ liệu thay đổi ở app demo, app quản lý cũng có thể nhìn thấy cùng nguồn dữ liệu đó.

## 5. Cách chạy nhanh

Nếu chạy riêng frontend tĩnh:

```bash
cd apps/demo-app
python -m http.server 3010
```

Hoặc chạy cùng toàn hệ thống:

```bash
cd infra/docker
docker compose up --build
```

Mở tại:

- `http://localhost:3010`

## 6. Tài khoản mẫu

- Nhân viên bán hàng: `staff@smartlive.vn / staff01`
- Khách hàng demo 1: `0901234567 / 123456`
- Khách hàng demo 2: `0912345678 / 123456`

Ngoài ra khách hàng có thể tự tạo tài khoản mới ngay trên giao diện.
