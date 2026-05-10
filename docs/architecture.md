# Kien truc rut gon

Project chi con luong chay chinh cho app livestream chatbot.

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

## Demo App

- Hien thi phong livestream demo.
- Hien thi san pham dang ban.
- Gui tin nhan khach hang toi chatbot.
- Hien thi tra loi cua `SmartLive AI`.
- Co fallback local khi backend chua chay.

## API Gateway

- Cho phep demo app goi API tu trinh duyet.
- Forward request chatbot toi AI Service.
- Route chinh: `POST /api/v1/chatbot/reply`.

## AI Service

- Nhan tin nhan khach hang.
- Nhan ngu canh san pham, gia live, ton kho va lich su chat.
- Phan loai intent: hoi gia, hoi ton kho, hoi ship, mua hang, tu van, khieu nai.
- Sinh cau tra loi chatbot.
- Tra ve `should_escalate = true` khi can nhan vien tiep quan.

## Luong xu ly

1. Khach gui tin nhan trong app livestream.
2. App goi API Gateway.
3. Gateway goi `ai-service /chatbot/reply`.
4. AI Service sinh cau tra loi theo san pham dang chon.
5. App hien thi phan hoi trong khung chat.
