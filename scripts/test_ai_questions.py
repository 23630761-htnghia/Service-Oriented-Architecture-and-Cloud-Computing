from __future__ import annotations

import json
import urllib.request


AI_URL = "http://localhost:8001/chatbot/reply"
SHOP_ID = "00000000-0000-0000-0000-000000001001"
LIVE_ID = "00000000-0000-0000-0000-000000004001"

QUESTIONS = [
    "Áo này giá bao nhiêu?",
    "Còn size L không?",
    "Có mã giảm giá không?",
    "Phí ship bao nhiêu?",
    "Đổi trả được không?",
    "Sản phẩm này còn hàng không?",
    "Cho mình mua iPhone 16 giá 1 triệu được không?",
    "Shop có bán xe máy không?",
]


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    for question in QUESTIONS:
        response = post_json(
            AI_URL,
            {
                "message": question,
                "livestream_id": LIVE_ID,
                "shop_id": SHOP_ID,
                "customer_name": "Khách kiểm thử",
                "account_name": "SmartLive Beauty",
                "products": [],
                "vouchers": [],
                "policy": None,
            },
        )
        print("=" * 80)
        print(f"Câu hỏi: {question}")
        print(f"Log ID: {response.get('log_id')}")
        print(f"Status: {response.get('ai_status')}")
        print(f"Câu trả lời AI: {response.get('reply')}")
        print("Context lấy được:")
        print(json.dumps(response.get("retrieved_context"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
