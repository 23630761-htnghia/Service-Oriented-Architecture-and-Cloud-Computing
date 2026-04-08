from __future__ import annotations

from pathlib import Path

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
PRICE_KEYWORDS = {"gia", "bao nhieu", "bn", "price", "ship"}
BUYING_KEYWORDS = {"mua", "dat", "chot", "lay", "ib", "inbox", "check inbox"}
CONSULT_KEYWORDS = {"tu van", "size", "mau", "con hang", "chi tiet", "shop oi"}
SPAM_KEYWORDS = {"spam", "kiem tien", "link", "telegram", "bitcoin", "http://", "https://"}
COMPLAINT_KEYWORDS = {"khieu nai", "loi", "khong dung", "giao cham", "hong", "lag"}
HIGH_PRIORITY_HINTS = {"ib", "inbox", "mua", "dat", "chot", "ship"}


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
    return " ".join(text.strip().lower().split())


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


def detect_sentiment_rule(text: str) -> str:
    positive_hits = sum(1 for keyword in POSITIVE_KEYWORDS if keyword in text)
    negative_hits = sum(1 for keyword in NEGATIVE_KEYWORDS if keyword in text)

    if negative_hits > positive_hits:
        return "negative"
    if positive_hits > negative_hits:
        return "positive"
    return "neutral"


def detect_intent_rule(text: str) -> str:
    if contains_any(text, SPAM_KEYWORDS):
        return "spam"
    if contains_any(text, COMPLAINT_KEYWORDS):
        return "complaint"
    if contains_any(text, BUYING_KEYWORDS):
        return "buying_intent"
    if contains_any(text, PRICE_KEYWORDS):
        return "ask_price"
    if contains_any(text, CONSULT_KEYWORDS):
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
        reasons.append("Khach hang dang hoi gia san pham.")
    elif intent == "consult_request":
        score += 20
        reasons.append("Khach hang can duoc tu van them.")
    elif intent == "complaint":
        score += 5
        reasons.append("Can uu tien cham soc vi co dau hieu phan hoi tieu cuc.")
    elif intent == "spam":
        score -= 60
        reasons.append("Comment co dau hieu spam.")

    if sentiment == "positive":
        score += 10
        reasons.append("Cam xuc tich cuc tang kha nang chuyen doi.")
    elif sentiment == "negative":
        score -= 10
        reasons.append("Cam xuc tieu cuc lam giam kha nang chot don.")

    high_priority_matches = sum(1 for keyword in HIGH_PRIORITY_HINTS if keyword in text)
    if high_priority_matches:
        score += min(high_priority_matches * 5, 15)
        reasons.append("Co tu khoa hanh dong manh nhu mua, inbox hoac dat hang.")

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
        return "Nhan vien nen inbox hoac xac nhan don ngay."
    if intent == "ask_price":
        return "Tra loi gia va goi y san pham lien quan."
    if intent == "consult_request":
        return "Hoi them nhu cau va tu van san pham phu hop."
    if intent == "complaint":
        return "Xu ly phan hoi uu tien cao de tranh mat khach."
    if intent == "spam":
        return "Danh dau spam va an hoac loc comment."
    if priority == "high":
        return "Dua vao hang doi uu tien cho nhan vien."
    return "Theo doi them trong dashboard."


def analyze_comment(request: CommentRequest) -> CommentAnalysis:
    normalized = normalize_text(request.comment)
    sentiment = detect_sentiment(normalized)
    intent = detect_intent(normalized)
    lead_score, reasons = score_comment(normalized, sentiment, intent)
    priority = choose_priority(lead_score, intent)
    suggested_action = choose_action(intent, priority)

    if INTENT_MODEL is not None:
        reasons.append("Intent duoc su doan boi model da train.")
    if SENTIMENT_MODEL is not None:
        reasons.append("Sentiment duoc su doan boi model da train.")
    if not reasons:
        reasons.append("Comment chua co dau hieu ro rang, can theo doi them.")

    return CommentAnalysis(
        comment=request.comment,
        sentiment=sentiment,
        intent=intent,
        lead_score=lead_score,
        priority=priority,
        reasons=reasons,
        suggested_action=suggested_action,
    )
