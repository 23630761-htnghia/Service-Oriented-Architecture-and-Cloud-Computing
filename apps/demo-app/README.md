# Demo App

Day la app demo livestream rieng, tach khoi app SmartLive chinh.

Muc dich:

- Mo phong buoi live khi khong the demo truc tiep tren Facebook hoac TikTok.
- Co 2 vai tro: `nhan vien live` va `khach hang`.
- Nhan vien live co the bat dau, ket thuc phien, bat camera, micro, ghim san pham va chan khach trong live.
- Khach hang co the tim phien live, tim san pham, xem goi y noi dung lien quan, comment va nhan tin voi shop.
- Phan nhan tin duoc ho tro boi ML theo kịch ban demo: khach co y dinh mua se duoc shop chu dong nhan tin mot lan trong moi phien live.

Cau truc:

- `frontend/`: app SmartLive quan ly livestream chinh.
- `apps/demo-app/`: app demo livestream de thuyet trinh.

Cach chay nhanh:

```bash
cd apps/demo-app
python -m http.server 3010
```

Sau do mo `http://localhost:3010`.

De demo 2 luong song song:

- Mo 2 tab hoac 2 cua so trinh duyet cung luc.
- Dang nhap 1 ben bang tai khoan `nhan vien live`, 1 ben bang tai khoan `khach hang`.
- Moi tab giu session rieng, nhung du lieu comment, chat, block va trang thai live se dong bo qua lai theo thoi gian thuc.
