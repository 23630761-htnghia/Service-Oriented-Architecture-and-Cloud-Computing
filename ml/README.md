# ML Training

Thư mục `ml/` chứa dữ liệu mẫu và script huấn luyện cho phần AI phân tích bình luận khách hàng.

## 1. Vai trò trong bài hiện tại

AI trong hệ thống hiện phục vụ các mục tiêu chính:

- phân tích bình luận của khách hàng trong phiên live
- nhận diện tín hiệu quan tâm hoặc nhu cầu mua hàng
- hỗ trợ backend quyết định khi nào nên mở đầu hội thoại với khách

App quản lý hiện không còn dùng các màn hình ML cũ như cân bằng viewer hay phân tích comment thủ công. Phần AI được đưa về đúng chức năng cấu hình:

- bật hoặc tắt AI
- chỉnh mẫu tin nhắn AI gửi khi mở đầu hội thoại

## 2. Cấu trúc

- `data/comments_labeled.csv`: dữ liệu comment đã gán nhãn
- `training/train_comment_models.py`: script huấn luyện model intent và sentiment
- `models/`: nơi lưu model sau khi train

## 3. Cách chạy huấn luyện

```bash
pip install -r backend/services/ai-service/requirements.txt
python ml/training/train_comment_models.py
```

## 4. Model được sử dụng

Sau khi train xong, `ai-service` sẽ load:

- `ml/models/intent_model.joblib`
- `ml/models/sentiment_model.joblib`

Nếu chưa có model, service sẽ fallback về rule-based analyzer để hệ thống vẫn hoạt động trong môi trường demo.
