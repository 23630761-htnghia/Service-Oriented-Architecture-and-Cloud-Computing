from __future__ import annotations

import unicodedata


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
    "hong",
}
PRICE_KEYWORDS = {"gia", "bao nhieu", "bn", "price", "uu dai", "giam gia"}
BUYING_KEYWORDS = {"mua", "dat", "chot", "lay", "ib", "inbox", "muon chot", "lay luon"}
CONSULT_KEYWORDS = {
    "tu van",
    "size",
    "mau",
    "con hang",
    "ton kho",
    "chi tiet",
    "shop oi",
    "phu hop",
}
SPAM_KEYWORDS = {"spam", "kiem tien", "telegram", "bitcoin", "http://", "https://"}
COMPLAINT_KEYWORDS = {"khieu nai", "loi", "khong dung", "giao cham", "hong", "lag"}


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.strip().lower())
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    normalized = normalized.replace("đ", "d")
    return " ".join(normalized.split())


def contains_any(text: str, keywords: set[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def detect_sentiment(text: str) -> str:
    positive_hits = sum(1 for keyword in POSITIVE_KEYWORDS if keyword in text)
    negative_hits = sum(1 for keyword in NEGATIVE_KEYWORDS if keyword in text)

    if negative_hits > positive_hits:
        return "negative"
    if positive_hits > negative_hits:
        return "positive"
    return "neutral"


def detect_intent(text: str) -> str:
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
