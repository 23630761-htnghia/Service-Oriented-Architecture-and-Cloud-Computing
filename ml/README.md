# ML Training

## Mục tiêu

Thư mục này chứa dữ liệu mẫu và script train cho phần AI phân tích comment.

## Cấu trúc

- `data/comments_labeled.csv`: dữ liệu comment đã gán nhãn.
- `training/train_comment_models.py`: script train intent và sentiment.
- `models/`: nơi lưu model sau khi train.

## Cách chạy

```bash
pip install -r services/ai-service/requirements.txt
python ml/training/train_comment_models.py
```

Sau khi train xong, `ai-service` sẽ tự động load:

- `ml/models/intent_model.joblib`
- `ml/models/sentiment_model.joblib`

Nếu chưa có model, service sẽ fallback về rule-based analyzer.
