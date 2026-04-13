# AI phân tích comment

## 1. Mục tiêu

Thành phần AI được thiết kế để hỗ trợ đội ngũ livestream nhận diện nhanh comment quan trọng, khách hàng tiềm năng và cân bằng lượng người xem giữa các tài khoản livestream để giảm lag.

## 2. Đầu vào

Mỗi comment sau khi đồng bộ có thể chứa:

- Nội dung comment
- Tên người dùng
- Thời gian
- Kênh livestream
- Tài khoản livestream
- Livestream ID

## 3. Đầu ra

Kết quả phân tích có thể gồm:

- `sentiment`: positive, neutral, negative
- `intent`: ask_price, buying_intent, consult_request, complaint, spam
- `lead_score`: 0-100
- `priority`: high, medium, low

## 4. AI chống lag bằng viewer balancing

Ngoài việc phân tích comment, AI service còn đánh giá tải của từng tài khoản livestream để đề xuất cách cân bằng viewer.

### Đầu vào

- `current_viewers`
- `max_capacity`
- `lag_signal`
- `engagement_rate`
- `manual_priority`
- `incoming_viewers`

### Đầu ra

- `target_viewers` cho từng tài khoản
- `transfer_plan` đề xuất chuyển bớt viewer
- `recommended_entry_account_id` là kênh nên ưu tiên nhận viewer mới
- `lag_risk` cho từng tài khoản

### Ý tưởng xử lý

- Tính `weighted_capacity` dựa trên sức chứa, dấu hiệu lag và mức độ engagement.
- Nếu một tài khoản có dấu hiệu quá tải, hệ thống đề xuất giảm viewer của tài khoản đó.
- Viewer mới sẽ được ưu tiên đưa vào tài khoản có khả năng tải tốt hơn.
- Có thể kết hợp với router, queue hoặc logic điều hướng ngoài hệ thống livestream để giảm hiện tượng lag cục bộ.

## 5. Cách xây dựng

Có 2 hướng:

### Hướng 1 - Rule-based + AI API

- Tiền xử lý văn bản.
- Nhận diện từ khóa quan trọng như `bao nhiêu`, `ib`, `mua`, `ship`.
- Gọi model NLP/API để phân loại intent và sentiment.
- Kết hợp rule để tính lead score.

Hướng này dễ làm, phù hợp đồ án và dễ demo.

### Hướng 2 - Fine-tune hoặc train model riêng

- Thu thập tập dữ liệu comment.
- Gán nhãn intent, sentiment.
- Train model phân loại.
- Triển khai model thành một service riêng.

Hướng này tốt hơn về học thuật nhưng tốn nhiều dữ liệu và thời gian.

## 6. Công thức chấm điểm gợi ý

Ví dụ:

- Hỏi giá: +25
- Hỏi cách mua: +30
- Yêu cầu inbox: +35
- Cảm xúc tích cực: +10
- Spam: -50
- Từ khóa gấp: +15

Tổng điểm được giới hạn trong khoảng 0-100.

## 7. Ví dụ output

### Comment 1

Input:
`Shop ơi sản phẩm này bao nhiêu vậy?`

Output:

- sentiment: neutral
- intent: ask_price
- lead_score: 72
- priority: medium

### Comment 2

Input:
`Ib minh nhe, minh muon dat 2 cai`

Output:

- sentiment: positive
- intent: buying_intent
- lead_score: 91
- priority: high

### Comment 3

Input:
`Spam link kiếm tiền online`

Output:

- sentiment: negative
- intent: spam
- lead_score: 3
- priority: low

### Viewer balancing

Input:

- tài khoản A: 900 viewer, max 850, lag signal 0.9
- tài khoản B: 350 viewer, max 900, lag signal 0.2
- viewer mới dự kiến: 300

Output mong đợi:

- hệ thống đánh dấu tài khoản A có nguy cơ lag cao
- đề xuất chuyển bớt viewer từ A sang B
- đề xuất tài khoản B là kênh ưu tiên nhận viewer mới
