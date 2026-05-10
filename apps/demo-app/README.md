# Demo App

`apps/demo-app` la ung dung livestream chatbot duy nhat cua project.

## Noi dung app

- Mot man livestream demo
- Danh sach san pham dang ban
- Khung chat de khach hang hoi gia, ton kho, ship, tu van va chot don
- Chatbot goi `POST /api/v1/chatbot/reply` qua API Gateway
- Fallback local neu backend chua chay

## Chay rieng giao dien

```bash
cd apps/demo-app
python -m http.server 3010
```

Mo:

```text
http://localhost:3010
```

De chatbot goi backend that, chay them AI service va API Gateway bang Docker Compose tai `infra/docker`.
