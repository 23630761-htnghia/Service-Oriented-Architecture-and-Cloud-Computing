from __future__ import annotations

from pathlib import Path
import unicodedata

import joblib

from app.schemas import CommentAnalysis, CommentRequest


POSITIVE_KEYWORDS = {
    "chốt",
    "mua",
    "đặt",
    "lấy",
    "ok",
    "tốt",
    "thích",
    "xinh",
    "đẹp",
    "ib",
    "inbox",
}
NEGATIVE_KEYWORDS = {
    "lỗi",
    "lag",
    "chán",
    "tệ",
    "không tốt",
    "giá cao",
    "thất vọng",
    "khiếu nại",
}
PRICE_KEYWORDS = {"giá", "bao nhiêu", "bn", "price", "ship"}
BUYING_KEYWORDS = {"mua", "đặt", "chốt", "lấy", "ib", "inbox", "check inbox"}
CONSULT_KEYWORDS = {"tư vấn", "size", "màu", "còn hàng", "chi tiết", "shop ơi"}
SPAM_KEYWORDS = {"spam", "kiếm tiền", "link", "telegram", "bitcoin", "http://", "https://"}
COMPLAINT_KEYWORDS = {"khiếu nại", "lỗi", "không đúng", "giao chậm", "hỏng", "lag"}
HIGH_PRIORITY_HINTS = {"ib", "inbox", "mua", "đặt", "chốt", "ship"}


def resolve_model_dir() -> Path:
    current = Path(__file__).resolve()
    candidates: list[Path] = []

    for parent in current.parents:
        candidates.append(parent / "ml" / "models")

    candidates.append(Path("/app/ml/models"))

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return current.parents[2] / "ml" / "models"


MODEL_DIR = resolve_model_dir()
INTENT_MODEL_PATH = MODEL_DIR / "intent_model.joblib"
SENTIMENT_MODEL_PATH = MODEL_DIR / "sentiment_model.joblib"


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.strip().lower())
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    normalized = normalized.replace("đ", "d")
    return " ".join(normalized.split())


def normalize_keywords(keywords: set[str]) -> set[str]:
    return {normalize_text(keyword) for keyword in keywords}


def contains_any(text: str, keywords: set[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def load_model(path: Path):
    if not path.exists():
        return None
    try:
        return joblib.load(path)
    except Exception:
        return None


INTENT_MODEL = load_model(INTENT_MODEL_PATH)
SENTIMENT_MODEL = load_model(SENTIMENT_MODEL_PATH)
NORMALIZED_POSITIVE_KEYWORDS = normalize_keywords(POSITIVE_KEYWORDS)
NORMALIZED_NEGATIVE_KEYWORDS = normalize_keywords(NEGATIVE_KEYWORDS)
NORMALIZED_PRICE_KEYWORDS = normalize_keywords(PRICE_KEYWORDS)
NORMALIZED_BUYING_KEYWORDS = normalize_keywords(BUYING_KEYWORDS)
NORMALIZED_CONSULT_KEYWORDS = normalize_keywords(CONSULT_KEYWORDS)
NORMALIZED_SPAM_KEYWORDS = normalize_keywords(SPAM_KEYWORDS)
NORMALIZED_COMPLAINT_KEYWORDS = normalize_keywords(COMPLAINT_KEYWORDS)
NORMALIZED_HIGH_PRIORITY_HINTS = normalize_keywords(HIGH_PRIORITY_HINTS)


def detect_sentiment_rule(text: str) -> str:
    positive_hits = sum(1 for keyword in NORMALIZED_POSITIVE_KEYWORDS if keyword in text)
    negative_hits = sum(1 for keyword in NORMALIZED_NEGATIVE_KEYWORDS if keyword in text)

    if negative_hits > positive_hits:
        return "negative"
    if positive_hits > negative_hits:
        return "positive"
    return "neutral"


def detect_intent_rule(text: str) -> str:
    if contains_any(text, NORMALIZED_SPAM_KEYWORDS):
        return "spam"
    if contains_any(text, NORMALIZED_COMPLAINT_KEYWORDS):
        return "complaint"
    if contains_any(text, NORMALIZED_BUYING_KEYWORDS):
        return "buying_intent"
    if contains_any(text, NORMALIZED_PRICE_KEYWORDS):
        return "ask_price"
    if contains_any(text, NORMALIZED_CONSULT_KEYWORDS):
        return "consult_request"
    return "other"


def detect_sentiment(text: str) -> str:
    if SENTIMENT_MODEL is not None:
        try:
            return str(SENTIMENT_MODEL.predict([text])[0])
        except Exception:
            pass
    return detect_sentiment_rule(text)


def detect_intent(text: str) -> str:
    if INTENT_MODEL is not None:
        try:
            return str(INTENT_MODEL.predict([text])[0])
        except Exception:
            pass
    return detect_intent_rule(text)


def score_comment(text: str, sentiment: str, intent: str) -> tuple[int, list[str]]:
    score = 20
    reasons: list[str] = []

    if intent == "buying_intent":
        score += 45
        reasons.append("Comment cho thấy ý định mua hàng rõ ràng.")
    elif intent == "ask_price":
        score += 25
        reasons.append("Khách hàng đang hỏi giá sản phẩm.")
    elif intent == "consult_request":
        score += 20
        reasons.append("Khách hàng cần được tư vấn thêm.")
    elif intent == "complaint":
        score += 5
        reasons.append("Cần ưu tiên chăm sóc vì có dấu hiệu phản hồi tiêu cực.")
    elif intent == "spam":
        score -= 60
        reasons.append("Comment có dấu hiệu spam.")

    if sentiment == "positive":
        score += 10
        reasons.append("Cảm xúc tích cực làm tăng khả năng chuyển đổi.")
    elif sentiment == "negative":
        score -= 10
        reasons.append("Cảm xúc tiêu cực làm giảm khả năng chốt đơn.")

    high_priority_matches = sum(1 for keyword in NORMALIZED_HIGH_PRIORITY_HINTS if keyword in text)
    if high_priority_matches:
        score += min(high_priority_matches * 5, 15)
        reasons.append("Có từ khóa hành động mạnh như mua, inbox hoặc đặt hàng.")

    score = max(0, min(score, 100))
    return score, reasons


def choose_priority(score: int, intent: str) -> str:
    if score >= 80 or intent == "complaint":
        return "high"
    if score >= 50:
        return "medium"
    return "low"


def choose_action(intent: str, priority: str) -> str:
    if intent == "buying_intent":
        return "Nhân viên nên inbox hoặc xác nhận đơn ngay."
    if intent == "ask_price":
        return "Trả lời giá và gợi ý sản phẩm liên quan."
    if intent == "consult_request":
        return "Hỏi thêm nhu cầu và tư vấn sản phẩm phù hợp."
    if intent == "complaint":
        return "Xử lý phản hồi ưu tiên cao để tránh mất khách."
    if intent == "spam":
        return "Đánh dấu spam và ẩn hoặc lọc comment."
    if priority == "high":
        return "Đưa vào hàng đợi ưu tiên cho nhân viên."
    return "Theo dõi thêm trong dashboard."


def analyze_comment(request: CommentRequest) -> CommentAnalysis:
    normalized = normalize_text(request.comment)
    sentiment = detect_sentiment(normalized)
    intent = detect_intent(normalized)
    lead_score, reasons = score_comment(normalized, sentiment, intent)
    priority = choose_priority(lead_score, intent)
    suggested_action = choose_action(intent, priority)

    if INTENT_MODEL is not None:
        reasons.append("Intent được suy đoán bởi model đã train.")
    if SENTIMENT_MODEL is not None:
        reasons.append("Sentiment được suy đoán bởi model đã train.")
    if not reasons:
        reasons.append("Comment chưa có dấu hiệu rõ ràng, cần theo dõi thêm.")

    return CommentAnalysis(
        comment=request.comment,
        sentiment=sentiment,
        intent=intent,
        lead_score=lead_score,
        priority=priority,
        reasons=reasons,
        suggested_action=suggested_action,
    )
