from __future__ import annotations

from pathlib import Path
import unicodedata

import joblib

from app.schemas import CommentAnalysis, CommentRequest


POSITIVE_KEYWORDS = {
    "chot",
    "mua",
    "dat",
    "lay",
    "ok",
    "tot",
    "thich",
    "xinh",
    "dep",
    "ib",
    "inbox",
}
NEGATIVE_KEYWORDS = {
    "loi",
    "lag",
    "chan",
    "te",
    "khong tot",
    "gia cao",
    "that vong",
    "khieu nai",
}
PRICE_KEYWORDS = {"gia", "bao nhieu", "bn", "price", "ship", "freeship"}
BUYING_KEYWORDS = {"mua", "dat", "chot", "lay", "ib", "inbox", "muon chot", "lay luon"}
CONSULT_KEYWORDS = {"tu van", "size", "mau", "con hang", "chi tiet", "shop oi", "da nhay cam", "thanh phan"}
SPAM_KEYWORDS = {"spam", "kiem tien", "link", "telegram", "bitcoin", "http://", "https://"}
COMPLAINT_KEYWORDS = {"khieu nai", "loi", "khong dung", "giao cham", "hong", "lag"}
HIGH_PRIORITY_HINTS = {"ib", "inbox", "mua", "dat", "chot", "ship", "lay luon"}


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
        reasons.append("Bình luận cho thấy ý định mua hàng rõ ràng.")
    elif intent == "ask_price":
        score += 25
        reasons.append("Khách hàng đang hỏi giá hoặc ưu đãi.")
    elif intent == "consult_request":
        score += 20
        reasons.append("Khách hàng cần được tư vấn thêm.")
    elif intent == "complaint":
        score += 5
        reasons.append("Bình luận mang tính phản hồi tiêu cực cần được ưu tiên.")
    elif intent == "spam":
        score -= 60
        reasons.append("Bình luận có dấu hiệu spam.")

    if sentiment == "positive":
        score += 10
        reasons.append("Cảm xúc tích cực tăng khả năng chuyển đổi.")
    elif sentiment == "negative":
        score -= 10
        reasons.append("Cảm xúc tiêu cực làm giảm khả năng chốt đơn.")

    high_priority_matches = sum(1 for keyword in NORMALIZED_HIGH_PRIORITY_HINTS if keyword in text)
    if high_priority_matches:
        score += min(high_priority_matches * 5, 15)
        reasons.append("Bình luận có từ khóa hành động mạnh như mua, chốt, lấy luôn hoặc inbox.")

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
        return "Ưu tiên trả lời riêng và xác nhận đơn ngay."
    if intent == "ask_price":
        return "Trả lời giá, ưu đãi và điều kiện giao hàng."
    if intent == "consult_request":
        return "Hỏi thêm nhu cầu và tư vấn sản phẩm phù hợp."
    if intent == "complaint":
        return "Cần nhân viên xử lý cẩn thận để tránh mất khách."
    if intent == "spam":
        return "Đánh dấu spam và không đưa vào hàng xử lý."
    if priority == "high":
        return "Đẩy vào hàng đợi ưu tiên cho người bán."
    return "Theo dõi thêm trong dashboard."


def should_auto_message(intent: str, score: int) -> bool:
    return intent == "buying_intent" or (intent == "ask_price" and score >= 70)


def build_auto_message(request: CommentRequest, intent: str, score: int) -> tuple[bool, str | None, str]:
    if not request.username:
        return False, None, "Chưa có username khách hàng nên hệ thống chưa tự động nhắn."

    if should_auto_message(intent, score):
        customer_name = request.username.strip() or "ban"
        message = (
            f"Chào {customer_name}, shop đã nhận được nhu cầu của bạn. "
            "Mình xin phép nhắn riêng để xác nhận số lượng, ưu đãi và hỗ trợ chốt đơn ngay trong phiên live."
        )
        return True, message, "Bình luận có tín hiệu mua hàng rõ ràng nên phù hợp để trả lời tự động."

    return False, None, "Bình luận chưa đủ tín hiệu mua ngay nên chưa tự động nhắn."


def analyze_comment(request: CommentRequest) -> CommentAnalysis:
    normalized = normalize_text(request.comment)
    sentiment = detect_sentiment(normalized)
    intent = detect_intent(normalized)
    lead_score, reasons = score_comment(normalized, sentiment, intent)
    priority = choose_priority(lead_score, intent)
    suggested_action = choose_action(intent, priority)
    auto_message_enabled, auto_message, auto_message_reason = build_auto_message(request, intent, lead_score)

    if INTENT_MODEL is not None:
        reasons.append("Intent được suy đoán bởi model đã train.")
    if SENTIMENT_MODEL is not None:
        reasons.append("Sentiment được suy đoán bởi model đã train.")
    if not reasons:
        reasons.append("Bình luận chưa có dấu hiệu rõ ràng, cần theo dõi thêm.")

    return CommentAnalysis(
        comment=request.comment,
        username=request.username,
        livestream_id=request.livestream_id,
        account_id=request.account_id,
        platform=request.platform,
        sentiment=sentiment,
        intent=intent,
        lead_score=lead_score,
        priority=priority,
        reasons=reasons,
        suggested_action=suggested_action,
        should_auto_message=auto_message_enabled,
        auto_message=auto_message,
        auto_message_reason=auto_message_reason,
    )
