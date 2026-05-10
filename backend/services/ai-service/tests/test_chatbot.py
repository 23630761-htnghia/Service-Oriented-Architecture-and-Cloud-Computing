from app.chatbot import build_chatbot_reply
from app.schemas import ChatProductContext, ChatbotReplyRequest


def product_context() -> ChatProductContext:
    return ChatProductContext(
        product_id="product-01",
        name="Serum Vitamin C",
        retail_price=169000,
        live_price=129000,
        stock_quantity=18,
    )


def test_chatbot_answers_price_with_product_context():
    response = build_chatbot_reply(
        ChatbotReplyRequest(
            message="Gia live bao nhieu shop?",
            customer_name="An",
            products=[product_context()],
        )
    )
    assert response.intent == "ask_price"
    assert response.used_product_id == "product-01"
    assert "129.000" in response.reply


def test_chatbot_treats_stock_question_as_product_support():
    response = build_chatbot_reply(
        ChatbotReplyRequest(
            message="con hang khong shop",
            customer_name="An",
            products=[product_context()],
        )
    )
    assert response.intent == "consult_request"
    assert response.should_escalate is False


def test_chatbot_escalates_handoff_request():
    response = build_chatbot_reply(
        ChatbotReplyRequest(
            message="Cho minh gap nhan vien tu van",
            customer_name="An",
            products=[product_context()],
        )
    )
    assert response.should_escalate is True
