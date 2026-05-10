# Backend

Backend hien chi giu 2 service can thiet cho app livestream chatbot:

- `services/ai-service`: sinh cau tra loi chatbot theo ngu canh san pham.
- `services/api-gateway`: expose API cho demo app va forward request toi AI service.

## Chay backend

```bash
cd backend
docker compose up --build
```

Cong mac dinh:

- API Gateway: `http://localhost:8000`
- AI Service: `http://localhost:8001`

API chinh:

```text
POST /api/v1/chatbot/reply
```

Neu muon chay ca app giao dien, dung compose trong `infra/docker`.
