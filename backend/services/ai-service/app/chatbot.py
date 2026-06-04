from __future__ import annotations

from app.analyzer import detect_intent, detect_sentiment, normalize_text
from app.ollama_client import OllamaError, generateReplyWithOllama
from app.prompt_builder import SYSTEM_PROMPT, buildSellingPrompt
from app.schemas import (
    ChatProductContext,
    ChatVoucherContext,
    ChatbotReplyRequest,
    ChatbotReplyResponse,
)


PROMPT_TEMPLATE = SYSTEM_PROMPT
FALLBACK_REPLY = "Thông tin này shop cần kiểm tra thêm, em đã chuyển câu hỏi cho người bán hỗ trợ ạ."

HUMAN_HANDOFF_KEYWORDS = {"nhan vien", "nguoi that", "tu van vien", "goi lai", "hotline"}
THANKS_KEYWORDS = {"cam on", "thanks", "thank", "ok shop", "da ro"}


def format_currency(value: float | None) -> str | None:
    if value is None:
        return None
    return f"{float(value):,.0f}".replace(",", ".") + " đ"


def customer_label(name: str | None) -> str:
    return name.strip() if name and name.strip() else "bạn"


def has_any(normalized_message: str, keywords: set[str]) -> bool:
    return any(keyword in normalized_message for keyword in keywords)


def choose_product(message: str, products: list[ChatProductContext]) -> ChatProductContext | None:
    if not products:
        return None

    normalized_message = normalize_text(message)
    best_product: ChatProductContext | None = None
    best_score = 0

    for product in products:
        searchable = " ".join(
            [
                product.name,
                product.category or "",
                product.brand or "",
                product.description or "",
                " ".join(product.variants),
            ]
        )
        tokens = {token for token in normalize_text(searchable).split() if len(token) >= 3}
        score = sum(1 for token in tokens if token in normalized_message)
        if product.product_id and normalize_text(product.product_id) in normalized_message:
            score += 4
        if score > best_score:
            best_score = score
            best_product = product

    return best_product or (products[0] if len(products) == 1 else None)


def vouchers_for_product(
    vouchers: list[ChatVoucherContext], product: ChatProductContext | None
) -> list[ChatVoucherContext]:
    active_vouchers = [voucher for voucher in vouchers if voucher.remaining_quantity is None or voucher.remaining_quantity > 0]
    if not product or not product.product_id:
        return [voucher for voucher in active_vouchers if not voucher.applicable_product_ids]
    return [
        voucher
        for voucher in active_vouchers
        if not voucher.applicable_product_ids or product.product_id in voucher.applicable_product_ids
    ]


def missing_data_reply(customer_name: str, topic: str) -> tuple[str, list[str]]:
    return (
        FALLBACK_REPLY,
        [f"Nhân viên cần bổ sung hoặc xác nhận dữ liệu {topic}."],
    )


def build_price_reply(
    customer_name: str,
    product: ChatProductContext | None,
    vouchers: list[ChatVoucherContext],
) -> tuple[str, list[str], bool, str | None]:
    if not product:
        return (*missing_data_reply(customer_name, "sản phẩm/giá"), True, None)

    price = format_currency(product.live_price or product.retail_price)
    if not price:
        return (*missing_data_reply(customer_name, f"giá của {product.name}"), True, None)

    label = customer_label(customer_name)
    reply = f"Dạ {label}, {product.name} hiện có giá "
    if product.live_price and product.retail_price and product.live_price < product.retail_price:
        reply += f"live {format_currency(product.live_price)} (giá gốc {format_currency(product.retail_price)})."
    else:
        reply += f"{price}."

    product_vouchers = vouchers_for_product(vouchers, product)
    used_voucher = product_vouchers[0].code if product_vouchers else None
    if product_vouchers:
        voucher = product_vouchers[0]
        reply += f" Bạn có thể dùng mã {voucher.code} để {voucher.discount_value}"
        if voucher.conditions:
            reply += f", điều kiện: {voucher.conditions}"
        reply += "."

    if product.purchase_url:
        reply += f" Link mua: {product.purchase_url}"
    else:
        reply += " Bạn nhắn số lượng muốn chốt để shop hỗ trợ ngay nhé."

    return reply, ["Gửi giá và nhắc khách chốt số lượng."], False, used_voucher


def build_stock_reply(customer_name: str, product: ChatProductContext | None) -> tuple[str, list[str], bool]:
    if not product:
        return (*missing_data_reply(customer_name, "tồn kho sản phẩm"), True)
    if product.stock_quantity is None:
        return (*missing_data_reply(customer_name, f"tồn kho của {product.name}"), True)

    label = customer_label(customer_name)
    if product.stock_quantity > 0:
        variants = f" Phân loại hiện có: {', '.join(product.variants)}." if product.variants else ""
        return (
            f"Dạ {label}, {product.name} còn {product.stock_quantity} sản phẩm.{variants} "
            "Bạn muốn chốt size/màu nào ạ?",
            ["Xác nhận size/màu và số lượng trước khi tạo đơn."],
            False,
        )
    return (
        f"Dạ {label}, {product.name} hiện tạm hết hàng. Mình sẽ chuyển nhân viên gợi ý sản phẩm thay thế phù hợp nhé.",
        ["Nhân viên nên gợi ý sản phẩm liên quan còn hàng."],
        True,
    )


def build_voucher_reply(
    customer_name: str,
    product: ChatProductContext | None,
    vouchers: list[ChatVoucherContext],
) -> tuple[str, list[str], bool, str | None]:
    product_vouchers = vouchers_for_product(vouchers, product)
    if not product_vouchers:
        return (*missing_data_reply(customer_name, "mã giảm giá phù hợp"), True, None)

    voucher = product_vouchers[0]
    label = customer_label(customer_name)
    product_note = f" cho {product.name}" if product else ""
    remaining = f", còn {voucher.remaining_quantity} lượt" if voucher.remaining_quantity is not None else ""
    until = f", hạn đến {voucher.valid_until}" if voucher.valid_until else ""
    conditions = f" Điều kiện: {voucher.conditions}." if voucher.conditions else ""
    return (
        f"Dạ {label}, mã đang áp dụng{product_note} là {voucher.code}: {voucher.discount_value}{remaining}{until}.{conditions} "
        "Bạn dùng mã này khi chốt đơn để được giảm nhé.",
        ["Nhắc khách nhập mã voucher khi chốt đơn."],
        False,
        voucher.code,
    )


def build_shipping_reply(customer_name: str, payload: ChatbotReplyRequest) -> tuple[str, list[str], bool]:
    policy = payload.policy
    if not policy or (not policy.shipping_fee_note and not policy.delivery_time_note):
        return (*missing_data_reply(customer_name, "phí ship/thời gian giao hàng"), True)

    label = customer_label(customer_name)
    notes = [note for note in [policy.shipping_fee_note, policy.delivery_time_note] if note]
    return (
        f"Dạ {label}, {' '.join(notes)} Bạn gửi khu vực nhận hàng để shop kiểm tra chính xác hơn nhé.",
        ["Xin khu vực nhận hàng để xác nhận phí ship."],
        False,
    )


def build_policy_reply(customer_name: str, payload: ChatbotReplyRequest) -> tuple[str, list[str], bool]:
    policy = payload.policy
    if not policy or not policy.return_policy:
        return (*missing_data_reply(customer_name, "chính sách đổi trả"), True)
    return (
        f"Dạ {customer_label(customer_name)}, chính sách đổi trả của shop: {policy.return_policy}",
        ["Nếu khách có đơn cụ thể, nhân viên nên kiểm tra mã đơn."],
        False,
    )


def build_buying_reply(
    customer_name: str,
    product: ChatProductContext | None,
    vouchers: list[ChatVoucherContext],
) -> tuple[str, list[str], bool, str | None]:
    if not product:
        return (*missing_data_reply(customer_name, "sản phẩm khách muốn chốt"), True, None)

    price = format_currency(product.live_price or product.retail_price)
    price_note = f" giá {price}" if price else ""
    voucher_note = ""
    used_voucher = None
    product_vouchers = vouchers_for_product(vouchers, product)
    if product_vouchers:
        used_voucher = product_vouchers[0].code
        voucher_note = f" Nhớ dùng mã {used_voucher} để được {product_vouchers[0].discount_value}."

    return (
        f"Dạ {customer_label(customer_name)}, shop ghi nhận bạn muốn chốt {product.name}{price_note}.{voucher_note} "
        "Bạn gửi số lượng, phân loại và địa chỉ nhận hàng để nhân viên xác nhận đơn nhé.",
        ["Tạo handoff cho nhân viên xác nhận thông tin giao hàng."],
        True,
        used_voucher,
    )


def build_consult_reply(
    customer_name: str,
    product: ChatProductContext | None,
    products: list[ChatProductContext],
) -> tuple[str, list[str], bool]:
    if not product:
        available = [item for item in products if item.stock_quantity is None or item.stock_quantity > 0]
        if not available:
            return (*missing_data_reply(customer_name, "sản phẩm để tư vấn"), True)
        names = ", ".join(item.name for item in available[:3])
        return (
            f"Dạ {customer_label(customer_name)}, hiện shop có thể tư vấn các sản phẩm: {names}. "
            "Bạn đang quan tâm loại nào để mình báo đúng thông tin ạ?",
            ["Hỏi khách chọn sản phẩm cụ thể."],
            False,
        )

    description = f" Điểm nổi bật: {product.description}" if product.description else ""
    variants = f" Có các phân loại: {', '.join(product.variants)}." if product.variants else ""
    return (
        f"Dạ {customer_label(customer_name)}, {product.name} phù hợp để tham khảo trong live này.{description}{variants} "
        "Bạn muốn mình báo giá, tồn kho hay link mua luôn ạ?",
        ["Gợi ý khách hỏi tiếp giá/tồn kho hoặc chốt đơn."],
        False,
    )


def _build_grounded_draft(payload: ChatbotReplyRequest) -> ChatbotReplyResponse:
    normalized_message = normalize_text(payload.message)
    product = choose_product(payload.message, payload.products)
    intent = detect_intent(normalized_message)
    sentiment = detect_sentiment(normalized_message)
    used_voucher_code: str | None = None
    confidence = 0.82

    if has_any(normalized_message, THANKS_KEYWORDS):
        reply = f"Dạ {customer_label(payload.customer_name)}, shop cảm ơn bạn. Cần thêm thông tin cứ nhắn tại đây nhé."
        actions: list[str] = []
        should_escalate = False
        confidence = 0.76
    elif has_any(normalized_message, HUMAN_HANDOFF_KEYWORDS):
        reply = (
            f"Dạ {customer_label(payload.customer_name)}, mình đã ghi nhận yêu cầu gặp nhân viên. "
            "Shop sẽ chuyển hội thoại này cho nhân viên phụ trách hỗ trợ trực tiếp nhé."
        )
        actions = ["Nhân viên nên tiếp quản hội thoại."]
        should_escalate = True
        confidence = 0.86
    elif intent == "out_of_scope":
        reply = "Dạ shop chỉ hỗ trợ thông tin sản phẩm, voucher, giao hàng, đổi trả và chốt đơn trong phiên live này ạ."
        actions = ["Theo dõi câu hỏi ngoài phạm vi bán hàng."]
        should_escalate = False
        confidence = 0.74
    elif intent == "spam":
        reply = "Dạ shop chỉ hỗ trợ nội dung liên quan đến mua hàng trong livestream này ạ."
        actions = ["Theo dõi spam nếu khách tiếp tục gửi nội dung không liên quan."]
        should_escalate = False
        confidence = 0.7
    elif intent == "complaint" or sentiment == "negative":
        reply = (
            f"Dạ {customer_label(payload.customer_name)}, shop xin lỗi vì trải nghiệm chưa tốt. "
            "Mình sẽ chuyển nhân viên kiểm tra và hỗ trợ bạn kỹ hơn nhé."
        )
        actions = ["Ưu tiên nhân viên xử lý phản hồi tiêu cực."]
        should_escalate = True
        confidence = 0.84
    elif intent == "ask_price":
        reply, actions, should_escalate, used_voucher_code = build_price_reply(
            payload.customer_name, product, payload.vouchers
        )
        confidence = 0.88 if not should_escalate else 0.55
    elif intent == "ask_stock":
        reply, actions, should_escalate = build_stock_reply(payload.customer_name, product)
        confidence = 0.86 if not should_escalate else 0.55
    elif intent == "ask_voucher":
        reply, actions, should_escalate, used_voucher_code = build_voucher_reply(
            payload.customer_name, product, payload.vouchers
        )
        confidence = 0.86 if not should_escalate else 0.55
    elif intent == "ask_shipping":
        reply, actions, should_escalate = build_shipping_reply(payload.customer_name, payload)
        confidence = 0.84 if not should_escalate else 0.55
    elif intent == "ask_policy":
        reply, actions, should_escalate = build_policy_reply(payload.customer_name, payload)
        confidence = 0.84 if not should_escalate else 0.55
    elif intent == "buying_intent":
        reply, actions, should_escalate, used_voucher_code = build_buying_reply(
            payload.customer_name, product, payload.vouchers
        )
        confidence = 0.88 if product else 0.55
    else:
        reply, actions, should_escalate = build_consult_reply(payload.customer_name, product, payload.products)
        confidence = 0.8 if not should_escalate else 0.55

    return ChatbotReplyResponse(
        reply=reply,
        intent=intent,
        sentiment=sentiment,
        confidence=confidence,
        should_escalate=should_escalate,
        suggested_actions=actions,
        used_product_id=product.product_id if product else None,
        used_voucher_code=used_voucher_code,
    )


def validateAIReply(reply: str, retrieved_context: dict) -> tuple[bool, str | None]:
    normalized = reply.strip()
    if not normalized:
        return False, "Ollama returned an empty reply"
    if len([sentence for sentence in normalized.replace("?", ".").replace("!", ".").split(".") if sentence.strip()]) > 4:
        return False, "Reply is too long for livestream chat"
    if "tôi là khách" in normalize_text(normalized):
        return False, "Reply appears to answer as the customer"
    if not retrieved_context.get("product") and not retrieved_context.get("policy") and not retrieved_context.get("vouchers"):
        return False, "No relevant database context was retrieved"
    return True, None


def build_chatbot_reply(payload: ChatbotReplyRequest) -> ChatbotReplyResponse:
    draft = _build_grounded_draft(payload)
    retrieved_context = retrieveRelevantShopData(payload)
    prompt = buildSellingPrompt(payload, retrieved_context)
    draft.retrieved_context = retrieved_context
    draft.prompt = prompt

    if draft.should_escalate:
        draft.reply = FALLBACK_REPLY if draft.reply == FALLBACK_REPLY else draft.reply
        draft.ai_status = "NEED_SELLER_SUPPORT"
        return draft

    try:
        ai_settings = payload.ai_settings
        ollama_reply, raw_response = generateReplyWithOllama(
            prompt,
            model_name=ai_settings.model_name if ai_settings else None,
            temperature=ai_settings.temperature if ai_settings else None,
            max_tokens=ai_settings.max_tokens if ai_settings else None,
        )
        is_valid, validation_error = validateAIReply(ollama_reply, retrieved_context)
        if not is_valid:
            raise OllamaError(validation_error or "Invalid Ollama reply")
        draft.reply = ollama_reply
        draft.raw_model_response = raw_response
        draft.ai_status = "ANSWERED"
        return draft
    except OllamaError as exc:
        draft.reply = FALLBACK_REPLY
        draft.confidence = 0.2
        draft.should_escalate = True
        draft.error_message = f"Ollama error: {exc}"
        draft.ai_status = "NEED_SELLER_SUPPORT"
        draft.suggested_actions = ["Ollama lỗi hoặc timeout, người bán cần tiếp quản câu hỏi."]
        return draft


def classifyCustomerQuestion(message: str) -> str:
    return detect_intent(normalize_text(message))


def retrieveRelevantShopData(payload: ChatbotReplyRequest) -> dict:
    product = choose_product(payload.message, payload.products)
    vector_context = retrieveVectorContext(payload)
    return {
        "product": product.model_dump() if product else None,
        "vouchers": [voucher.model_dump() for voucher in vouchers_for_product(payload.vouchers, product)],
        "policy": payload.policy.model_dump() if payload.policy else None,
        "vector_context": vector_context,
    }


def retrieveVectorContext(payload: ChatbotReplyRequest) -> list[dict]:
    """RAG hook for pgvector-backed retrieval.

    In the local demo we do not call an embedding model. Instead, this returns
    the same shape expected from a pgvector similarity query so the AI pipeline
    and logs clearly show where vector context is attached.
    """
    normalized_message = normalize_text(payload.message)
    candidates: list[dict] = []
    for product in payload.products:
        searchable = normalize_text(" ".join([product.name, product.description or "", product.category or ""]))
        score = sum(1 for token in normalized_message.split() if token and token in searchable)
        if score > 0:
            candidates.append(
                {
                    "type": "product",
                    "id": product.product_id,
                    "title": product.name,
                    "content": product.description,
                    "similarity_score": min(1.0, score / 8),
                }
            )
    if payload.policy:
        candidates.append(
            {
                "type": "policy",
                "id": "sales-policy",
                "title": "Chính sách bán hàng",
                "content": payload.policy.model_dump(),
                "similarity_score": 0.6,
            }
        )
    return sorted(candidates, key=lambda item: item["similarity_score"], reverse=True)[:5]


def generateAIReply(payload: ChatbotReplyRequest) -> ChatbotReplyResponse:
    return build_chatbot_reply(payload)


def saveAIResponseLog(response: ChatbotReplyResponse) -> dict:
    return {
        "confidence_score": response.confidence,
        "status": "NEED_SELLER_SUPPORT" if response.should_escalate else "ANSWERED",
        "intent": response.intent,
        "used_product_id": response.used_product_id,
        "used_voucher_code": response.used_voucher_code,
    }


def escalateToSellerIfNeeded(response: ChatbotReplyResponse) -> bool:
    return response.should_escalate
