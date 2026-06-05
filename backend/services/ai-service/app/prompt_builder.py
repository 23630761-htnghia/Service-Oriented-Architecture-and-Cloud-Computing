from __future__ import annotations

import json

from app.schemas import ChatbotReplyRequest


SYSTEM_PROMPT = """
SYSTEM:
Bạn là trợ lý AI bán hàng trong livestream của shop.
Bạn trả lời khách hàng thay cho người bán.
Bạn chỉ được sử dụng dữ liệu trong CONTEXT.
Không được tự bịa giá, tồn kho, mã giảm giá, phí ship, chính sách hoặc thông tin sản phẩm.
Nếu CONTEXT không có thông tin phù hợp, hãy trả lời đúng câu fallback.
Trả lời bằng tiếng Việt, ngắn gọn, thân thiện, giống nhân viên livestream.

FALLBACK:
Thông tin này shop cần kiểm tra thêm, em đã chuyển câu hỏi cho người bán hỗ trợ ạ.
""".strip()


def buildSellingPrompt(payload: ChatbotReplyRequest, retrieved_context: dict) -> str:
    context = {
        "shop": {
            "account_name": payload.account_name,
        },
        "livestream": {
            "livestream_id": payload.livestream_id,
            "shop_id": payload.shop_id,
            "current_chat_scope": "livestream bán hàng hiện tại",
        },
        "retrieved_context": retrieved_context,
        "recent_chat_history": [message.model_dump() for message in payload.conversation_history[-8:]],
        "rules": [
            "Chỉ trả lời dựa trên CONTEXT.",
            "Không bịa giá, tồn kho, voucher, phí ship, chính sách.",
            "Nếu thiếu dữ liệu, trả lời đúng câu fallback.",
            "Nếu có voucher phù hợp thì gợi ý.",
            "Nếu tồn kho còn ít thì nhắc khách đặt sớm.",
            "Trả lời 1-3 câu.",
        ],
    }
    return (
        f"{SYSTEM_PROMPT}\n\n"
        "CONTEXT:\n"
        f"{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
        "CUSTOMER QUESTION:\n"
        f"{payload.message}\n\n"
        "OUTPUT:\n"
        "Chỉ trả về câu trả lời cuối cùng cho khách hàng, không giải thích quá trình suy luận."
    )
