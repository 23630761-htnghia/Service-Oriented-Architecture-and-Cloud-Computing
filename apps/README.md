# Apps

Thư mục `apps/` chứa các ứng dụng phụ hoặc ứng dụng mô phỏng tách riêng khỏi app quản lý chính.

## Hiện tại có

- `demo-app/`: ứng dụng livestream demo phục vụ thuyết trình và mô phỏng phiên live

## Vai trò của demo app trong bài hiện tại

`demo-app` không còn là một bản demo chạy tách biệt bằng dữ liệu giả. Ứng dụng này dùng chung backend với app quản lý để mô phỏng:

- nhân viên bán hàng lên live
- khách hàng vào xem live
- bình luận trong phòng live
- AI mở đầu hội thoại khi phát hiện khách quan tâm
- nhắn tin giữa shop và khách hàng
- thêm sản phẩm vào giỏ hàng và checkout
- đồng bộ viewer theo presence thật

## Vai trò sử dụng trong demo app

- `Nhân viên bán hàng`
- `Khách hàng`

`Admin` và `quản lý sản phẩm` không đăng nhập tại đây, mà dùng app quản lý chính trong `frontend/`.
