# SmartLive Chatbot Livestream

Project da duoc don gon de tap trung vao mot muc tieu duy nhat: app livestream ban hang co chatbot tu dong tra loi khach hang.

## Thanh phan hien con

```text
apps/demo-app                 App livestream chatbot
backend/services/ai-service   AI chatbot service
backend/services/api-gateway  Gateway cho demo app goi AI
infra/docker                  Docker Compose chay toan bo app
docs                          Tai lieu kien truc rut gon
```

Nhung phan cu khong phuc vu livestream chatbot da duoc loai bo khoi luong chay chinh.

## Chuc nang chinh

- Hien thi mot phong livestream demo.
- Cho phep chon san pham dang ban.
- Khach hang hoi chatbot ve gia live, ton kho, phi ship, tu van va chot don.
- Chatbot tra loi dua tren san pham dang chon va lich su chat gan nhat.
- Khi backend chua chay, demo app co fallback local de van demo duoc.

## Kien truc

```text
Browser
  |
  v
Demo App :3010
  |
  v
API Gateway :8000
  |
  v
AI Service :8001
```

API chinh:

```text
POST /api/v1/chatbot/reply
```

## Chay bang Docker

```bash
cd infra/docker
docker compose up --build
```

Mo app:

```text
http://localhost:3010
```

Tai lieu API:

```text
http://localhost:8001/docs
```

## Chay thu giao dien rieng

```bash
cd apps/demo-app
python -m http.server 3010
```

Mo `http://localhost:3010`.

Luu y: neu chi chay giao dien, chatbot se dung fallback local. De goi AI service that, hay chay Docker Compose.

## Cau hoi demo goi y

- `gia live bao nhieu`
- `con hang khong shop`
- `co ship quan 7 khong`
- `tu van san pham nay phu hop voi ai`
- `minh muon chot 1 san pham`
- `cho minh gap nhan vien tu van`

## Kiem tra nhanh

```bash
node --check apps/demo-app/app.js
cd backend/services/ai-service
python -m compileall app tests
```
