# Demo App

Đây là app demo livestream riêng, tách khỏi app SmartLive chính.

## Mục đích

- Mô phỏng buổi live khi không thể demo trực tiếp trên Facebook hoặc TikTok.
- Có 3 vai trò chính: `nhân viên live`, `khách hàng`, `quản lý sản phẩm`.
- Nhân viên live có thể bắt đầu, kết thúc phiên, bật camera, micro, ghim sản phẩm và xử lý hội thoại với khách.
- Khách hàng có thể tìm phiên live, tìm sản phẩm, xem gợi ý nội dung liên quan, bình luận và nhắn tin với shop.
- Quản lý sản phẩm có thể thêm sản phẩm, tăng tồn kho và gán sản phẩm vào từng phiên live trước khi bán.

## Vị trí trong project

- `frontend/`: app SmartLive quản lý livestream chính.
- `apps/demo-app/`: app demo livestream để thuyết trình và mô phỏng luồng thực tế.

## Chạy nhanh

```bash
cd apps/demo-app
python -m http.server 3010
```

Sau đó mở:

- `http://localhost:3010`

## Cách demo song song

- Mở 2 tab hoặc 2 cửa sổ trình duyệt cùng lúc.
- Đăng nhập một bên bằng tài khoản `nhân viên live`, một bên bằng tài khoản `khách hàng`.
- Mỗi tab giữ session riêng, nhưng dữ liệu bình luận, hội thoại, giỏ hàng và trạng thái live sẽ đồng bộ qua backend.
