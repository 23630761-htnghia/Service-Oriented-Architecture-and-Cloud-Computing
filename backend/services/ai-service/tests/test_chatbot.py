from app.chatbot import build_chatbot_reply
from app.schemas import ChatProductContext, ChatVoucherContext, ChatbotReplyRequest, SalesPolicyContext


def product_context() -> ChatProductContext:
    return ChatProductContext(
        product_id="product-01",
        name="Serum Vitamin C",
        retail_price=169000,
        live_price=129000,
        stock_quantity=18,
        variants=["30ml"],
    )


def voucher_context() -> ChatVoucherContext:
    return ChatVoucherContext(
        voucher_id="voucher-01",
        code="LIVE20",
        discount_value="giam 20.000d",
        conditions="don tu 199.000d",
        remaining_quantity=10,
    )


def test_chatbot_answers_price_with_product_context(monkeypatch):
    monkeypatch.setattr("app.chatbot.generateReplyWithOllama", lambda prompt, **kwargs: ("Dạ Serum đang có giá live 129.000 đ ạ.", "Dạ Serum đang có giá live 129.000 đ ạ."))
    response = build_chatbot_reply(
        ChatbotReplyRequest(
            message="Gia live bao nhieu shop?",
            customer_name="An",
            products=[product_context()],
            vouchers=[voucher_context()],
        )
    )
    assert response.intent == "ask_price"
    assert response.used_product_id == "product-01"
    assert "129.000" in response.reply
    assert response.ai_status == "ANSWERED"


def test_chatbot_treats_stock_question_as_product_support(monkeypatch):
    monkeypatch.setattr("app.chatbot.generateReplyWithOllama", lambda prompt, **kwargs: ("Dạ sản phẩm còn hàng, bạn chốt sớm giúp shop nhé.", "Dạ sản phẩm còn hàng, bạn chốt sớm giúp shop nhé."))
    response = build_chatbot_reply(
        ChatbotReplyRequest(
            message="con hang khong shop",
            customer_name="An",
            products=[product_context()],
        )
    )
    assert response.intent == "ask_stock"
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


def test_chatbot_escalates_when_ollama_fails(monkeypatch):
    from app.ollama_client import OllamaError

    def raise_error(prompt, **kwargs):
        raise OllamaError("timeout")

    monkeypatch.setattr("app.chatbot.generateReplyWithOllama", raise_error)
    response = build_chatbot_reply(
        ChatbotReplyRequest(
            message="Gia live bao nhieu shop?",
            customer_name="An",
            products=[product_context()],
        )
    )
    assert response.should_escalate is True
    assert response.ai_status == "NEED_SELLER_SUPPORT"
    assert "shop cần kiểm tra thêm" in response.reply


def test_chatbot_escalates_when_shipping_policy_is_missing():
    response = build_chatbot_reply(
        ChatbotReplyRequest(
            message="co ship quan 7 khong",
            customer_name="An",
            products=[product_context()],
        )
    )
    assert response.intent == "ask_shipping"
    assert response.should_escalate is True


def test_chatbot_answers_policy_from_context(monkeypatch):
    monkeypatch.setattr("app.chatbot.generateReplyWithOllama", lambda prompt, **kwargs: ("Doi tra trong 7 ngay neu san pham loi.", "Doi tra trong 7 ngay neu san pham loi."))
    response = build_chatbot_reply(
        ChatbotReplyRequest(
            message="doi tra nhu the nao",
            customer_name="An",
            products=[product_context()],
            policy=SalesPolicyContext(return_policy="Doi tra trong 7 ngay neu san pham loi."),
        )
    )
    assert response.intent == "ask_policy"
    assert response.should_escalate is False
    assert "7" in response.reply
