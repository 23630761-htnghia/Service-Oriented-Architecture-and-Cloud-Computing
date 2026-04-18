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
        reasons.append("Comment cho thay y dinh mua hang ro rang.")
    elif intent == "ask_price":
        score += 25
        reasons.append("Khach hang dang hoi gia hoac uu dai.")
    elif intent == "consult_request":
        score += 20
        reasons.append("Khach hang can duoc tu van them.")
    elif intent == "complaint":
        score += 5
        reasons.append("Comment mang tinh phan hoi tieu cuc can duoc uu tien.")
    elif intent == "spam":
        score -= 60
        reasons.append("Comment co dau hieu spam.")

    if sentiment == "positive":
        score += 10
        reasons.append("Cam xuc tich cuc tang kha nang chuyen doi.")
    elif sentiment == "negative":
        score -= 10
        reasons.append("Cam xuc tieu cuc lam giam kha nang chot don.")

    high_priority_matches = sum(1 for keyword in NORMALIZED_HIGH_PRIORITY_HINTS if keyword in text)
    if high_priority_matches:
        score += min(high_priority_matches * 5, 15)
        reasons.append("Comment co tu khoa hanh dong manh nhu mua, chot, lay luon hoac inbox.")

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
        return "Uu tien tra loi rieng va xac nhan don ngay."
    if intent == "ask_price":
        return "Tra loi gia, uu dai va dieu kien giao hang."
    if intent == "consult_request":
        return "Hoi them nhu cau va tu van san pham phu hop."
    if intent == "complaint":
        return "Can nhan vien xu ly can than de tranh mat khach."
    if intent == "spam":
        return "Danh dau spam va khong dua vao hang xu ly."
    if priority == "high":
        return "Day vao hang doi uu tien cho nguoi ban."
    return "Theo doi them trong dashboard."


def should_auto_message(intent: str, score: int) -> bool:
    return intent == "buying_intent" or (intent == "ask_price" and score >= 70)


def build_auto_message(request: CommentRequest, intent: str, score: int) -> tuple[bool, str | None, str]:
    if not request.username:
        return False, None, "Chua co username khach hang nen he thong chua tu dong nhan."

    if should_auto_message(intent, score):
        customer_name = request.username.strip() or "ban"
        message = (
            f"Chao {customer_name}, shop da nhan duoc nhu cau cua ban. "
            "Minh xin phep nhan rieng de xac nhan so luong, uu dai va ho tro chot don ngay trong phien live."
        )
        return True, message, "Comment co tin hieu mua hang ro rang nen phu hop de tra loi tu dong."

    return False, None, "Comment chua du tin hieu mua ngay nen chua tu dong nhan."


def analyze_comment(request: CommentRequest) -> CommentAnalysis:
    normalized = normalize_text(request.comment)
    sentiment = detect_sentiment(normalized)
    intent = detect_intent(normalized)
    lead_score, reasons = score_comment(normalized, sentiment, intent)
    priority = choose_priority(lead_score, intent)
    suggested_action = choose_action(intent, priority)
    auto_message_enabled, auto_message, auto_message_reason = build_auto_message(request, intent, lead_score)

    if INTENT_MODEL is not None:
        reasons.append("Intent duoc suy doan boi model da train.")
    if SENTIMENT_MODEL is not None:
        reasons.append("Sentiment duoc suy doan boi model da train.")
    if not reasons:
        reasons.append("Comment chua co dau hieu ro rang, can theo doi them.")

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
