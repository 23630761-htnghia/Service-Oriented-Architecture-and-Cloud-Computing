# Kiến trúc hệ thống

## 1. Mô hình tổng thể

Hệ thống được chia thành các thành phần độc lập để dễ mở rộng, bảo trì và triển khai:

- Frontend Dashboard
- API Gateway
- Auth Service
- Account Service
- Livestream Sync Service
- Comment Analysis Service
- Lead Scoring Service
- Viewer Balancing AI Module
- Notification Service
- Reporting Service
- PostgreSQL
- Redis
- Object Storage

## 2. Vai trò từng service

### API Gateway

- Tiếp nhận request từ frontend.
- Xác thực token và định tuyến request đến service phù hợp.
- Có thể bổ sung rate limiting và logging.

### Auth Service

- Đăng ký, đăng nhập, refresh token.
- Quản lý vai trò: admin, staff, analyst.

### Account Service

- Quản lý thông tin shop.
- Quản lý danh sách tài khoản livestream.
- Lưu cấu hình kết nối đến các nền tảng.

### Livestream Sync Service

- Thu nhận comment, sự kiện từ livestream.
- Chuẩn hóa dữ liệu comment về một định dạng thống nhất.
- Đẩy sự kiện sang queue để xử lý tiếp.

### Comment Analysis Service

- Làm sạch comment.
- Phân tích sentiment.
- Nhận diện intent.
- Chuyển kết quả sang service chấm điểm lead.

### Lead Scoring Service

- Tính điểm tiềm năng của khách hàng.
- Ưu tiên lead cho đội ngũ bán hàng.
- Áp dụng rule engine kết hợp AI.

### Viewer Balancing AI Module

- Đánh giá sức tải của từng tài khoản livestream.
- Ước lượng nguy cơ lag dựa trên viewer, capacity và lag signal.
- Đề xuất phân bổ viewer mới vào tài khoản ổn định hơn.
- Hỗ trợ giảm quá tải khi một kênh đang tăng đột biến.

### Notification Service

- Cảnh báo khi có lead điểm cao.
- Gửi thông báo trên dashboard hoặc email.

### Reporting Service

- Tổng hợp KPI livestream.
- Thống kê số comment, số lead, top livestream.

## 3. Luồng dữ liệu đề xuất

1. Tài khoản livestream phát sinh comment.
2. Sync Service thu nhận và chuẩn hóa comment.
3. Comment được đẩy vào Redis/RabbitMQ.
4. AI Service đọc comment và phân tích.
5. Lead Scoring Service chấm điểm.
6. Viewer Balancing Module tính toán phân bổ viewer để tránh lag.
7. Kết quả được lưu vào PostgreSQL.
8. Frontend hiển thị comment và dashboard theo thời gian gần realtime.

## 4. Kiến trúc triển khai

- Frontend: một ứng dụng web.
- Các service backend: deploy độc lập bằng container.
- Database và Redis: sử dụng managed service nếu deploy cloud.
- Monitoring: Prometheus + Grafana hoặc cloud monitoring.

## 5. Sơ đồ logic

```text
Frontend Dashboard
        |
        v
    API Gateway
        |
        +--------------------+
        |                    |
        v                    v
 Auth Service         Account Service
                              |
                              v
                    Livestream Sync Service
                              |
                              v
                       Queue / Redis
                              |
                 +------------+------------+
                 |                         |
                 v                         v
      Comment Analysis Service   Lead Scoring Service
                 |                         |
                 +------------+------------+
                              |
                              v
                  Viewer Balancing AI Module
                              |
                              v
                         PostgreSQL
                              |
                              v
                      Reporting Service
                              |
                              v
                      Frontend Dashboard
```

## 6. Sơ đồ kiến trúc SOA/Microservices

```mermaid
flowchart LR
    U[User / Staff / Admin] --> FE[Frontend Dashboard]
    FE --> GW[API Gateway]

    GW --> AUTH[Auth Service]
    GW --> ACC[Account Service]
    GW --> SYNC[Livestream Sync Service]
    GW --> AI[Comment Analysis Service]
    GW --> LEAD[Lead Scoring Service]
    GW --> VIEWER[Viewer Balancing AI Module]
    GW --> NOTI[Notification Service]
    GW --> REPORT[Reporting Service]

    PLATFORM[Livestream Platforms\nTikTok / Facebook / Shopee Live] --> SYNC
    SYNC --> MQ[Redis / Queue]
    MQ --> AI
    AI --> LEAD
    LEAD --> NOTI
    LEAD --> REPORT
    VIEWER --> REPORT

    ACC --> DB[(PostgreSQL)]
    AUTH --> DB
    AI --> DB
    LEAD --> DB
    REPORT --> DB

    AI --> CACHE[(Redis Cache)]
    SYNC --> OBJ[(Object Storage)]
    REPORT --> OBJ

    REPORT --> FE
    NOTI --> FE
```

Sơ đồ này thể hiện hệ thống theo hướng kiến trúc dịch vụ, trong đó mỗi service đảm nhận một nghiệp vụ riêng và có thể được triển khai, mở rộng, giám sát độc lập.

## 7. Sơ đồ kiến trúc tổng thể (services, APIs, data flow, integration)

```mermaid
flowchart TB
    subgraph Clients[Client Layer]
        USER[Admin / Staff / Analyst]
        WEB[Frontend Dashboard]
    end

    subgraph Gateway[Access Layer]
        APIGW[API Gateway\nREST APIs\nAuth check / routing / logging]
    end

    subgraph Core[Business Services]
        AUTH[Auth Service\n/login /refresh /me]
        ACC[Account Service\n/accounts /platforms /shops]
        SYNC[Livestream Sync Service\n/webhooks /comments /streams]
        AI[Comment Analysis Service\n/analyze-comment /predict]
        LEAD[Lead Scoring Service\n/lead-score /prioritize]
        VIEWER[Viewer Balancing AI Module\n/balance-viewers /lag-risk]
        NOTI[Notification Service\n/alerts /push]
        REPORT[Reporting Service\n/reports /kpi /dashboard]
    end

    subgraph Integration[External Integration]
        LIVE[Livestream Platforms\nTikTok / Facebook / Shopee Live]
        EMAIL[Email / Realtime Notification]
    end

    subgraph Data[Data Layer]
        REDIS[(Redis / Queue)]
        PG[(PostgreSQL)]
        OBJ[(Object Storage)]
        MODEL[(ML Models)]
    end

    USER --> WEB
    WEB -->|HTTP/JSON| APIGW

    APIGW -->|REST API| AUTH
    APIGW -->|REST API| ACC
    APIGW -->|REST API| SYNC
    APIGW -->|REST API| AI
    APIGW -->|REST API| LEAD
    APIGW -->|REST API| VIEWER
    APIGW -->|REST API| REPORT
    APIGW -->|REST API| NOTI

    LIVE -->|Webhook / polling events| SYNC
    SYNC -->|normalized comments| REDIS
    REDIS -->|stream event| AI
    AI -->|intent + sentiment| LEAD
    AI -->|load inference model| MODEL
    LEAD -->|high-priority leads| NOTI
    LEAD -->|lead result| PG
    VIEWER -->|lag-risk + transfer plan| PG
    REPORT -->|read KPIs| PG
    REPORT -->|export files| OBJ
    SYNC -->|raw data / backup| OBJ

    AUTH -->|user / role data| PG
    ACC -->|shop / account config| PG
    AI -->|analysis result cache| REDIS
    NOTI -->|push alert / email| EMAIL

    PG --> REPORT
    PG --> WEB
    NOTI --> WEB
```

Sơ đồ này nhấn mạnh 4 thành phần chính:

- `services`: các service được tách theo nghiệp vụ riêng.
- `APIs`: frontend và gateway giao tiếp với backend bằng REST API.
- `data flow`: comment đi từ livestream platform qua sync service, vào queue, sang AI, chấm điểm lead, lưu vào database và hiển thị lên dashboard.
- `integration`: hệ thống kết nối với nền tảng livestream bên ngoài, email/thông báo, object storage và model AI.
