from __future__ import annotations

from app.analyzer import detect_intent, detect_sentiment, normalize_text
from app.schemas import ChatProductContext, ChatbotReplyRequest, ChatbotReplyResponse


SHIPPING_KEYWORDS = {"ship", "giao", "freeship", "van chuyen", "phi ship", "nhan hang"}
STOCK_KEYWORDS = {"con hang", "het hang", "ton kho", "co san", "available"}
ORDER_KEYWORDS = {"dat hang", "chot don", "mua ngay", "thanh toan"}
THANKS_KEYWORDS = {"cam on", "thanks", "thank", "ok shop", "da ro"}
HUMAN_HANDOFF_KEYWORDS = {"nhan vien", "nguoi that", "tu van vien", "goi lai", "hotline"}
PRICE_KEYWORDS = {"gia", "bao nhieu", "bn", "price", "uu dai", "giam gia"}
BUYING_KEYWORDS = {"mua", "dat", "chot", "lay", "lay luon", "chot don"}


def format_currency(value: float | None) -> str | None:
    if value is None:
        return None
    return f"{float(value):,.0f}".replace(",", ".") + " đ"


def product_price(product: ChatProductContext | None) -> tuple[str | None, str | None]:
    if not product:
        return None, None
    live_price = format_currency(product.live_price)
    retail_price = format_currency(product.retail_price)
    return live_price or retail_price, retail_price


def choose_product(message: str, products: list[ChatProductContext]) -> ChatProductContext | None:
    if not products:
        return None

    normalized_message = normalize_text(message)
    best_product = products[0]
    best_score = -1.0

    for product in products:
        product_text = normalize_text(
            " ".join(
                value
                for value in [
                    product.name,
                    product.category or "",
                    product.brand or "",
                    product.description or "",
                ]
                if value
            )
        )
        tokens = {token for token in product_text.split() if len(token) >= 3}
        score = sum(1 for token in tokens if token in normalized_message)
        if product.live_price is not None:
            score += 0.25
        if score > best_score:
            best_score = score
            best_product = product

    return best_product


def has_any(normalized_message: str, keywords: set[str]) -> bool:
    return any(keyword in normalized_message for keyword in keywords)


def customer_label(name: str | None) -> str:
    return name.strip() if name and name.strip() else "bạn"


def build_price_reply(customer_name: str, product: ChatProductContext | None) -> str:
    label = customer_label(customer_name)
    if not product:
        return (
            f"Dạ {label}, shop đã nhận được câu hỏi về giá. "
            "Bạn cho shop biết sản phẩm đang quan tâm để mình báo đúng giá live và ưu đãi hiện tại nhé."
        )

    current_price, retail_price = product_price(product)
    stock_note = ""
    if product.stock_quantity is not None:
        stock_note = " Sản phẩm hiện còn hàng." if product.stock_quantity > 0 else " Sản phẩm này hiện tạm hết hàng."

    if product.live_price is not None and product.retail_price and product.live_price < product.retail_price:
        return (
            f"Dạ {label}, {product.name} đang có giá live {current_price} "
            f"(giá niêm yết {retail_price}).{stock_note} "
            "Bạn nhắn số lượng và khu vực nhận hàng để shop hỗ trợ chốt đơn."
        )

    return (
        f"Dạ {label}, {product.name} hiện có giá {current_price}.{stock_note} "
        "Bạn cần shop giữ hàng hoặc tư vấn thêm cách dùng thì nhắn mình nhé."
    )


def build_buying_reply(customer_name: str, product: ChatProductContext | None) -> str:
    label = customer_label(customer_name)
    if not product:
        return (
            f"Dạ {label}, shop đã nhận được nhu cầu đặt hàng. "
            "Bạn gửi giúp tên sản phẩm và số lượng, shop sẽ hỗ trợ xác nhận đơn ngay trong phiên live."
        )

    current_price, _retail_price = product_price(product)
    price_note = f" giá live {current_price}" if current_price else ""
    return (
        f"Dạ {label}, shop ghi nhận bạn muốn chốt {product.name}{price_note}. "
        "Bạn gửi số lượng và địa chỉ nhận hàng để shop hỗ trợ xác nhận."
    )


def build_consult_reply(customer_name: str, product: ChatProductContext | None) -> str:
    label = customer_label(customer_name)
    if not product:
        return (
            f"Dạ {label}, shop sẵn sàng tư vấn. "
            "Bạn cho mình biết nhu cầu, ngân sách hoặc sản phẩm đang xem để shop gợi ý đúng hơn nhé."
        )

    description = f" Điểm nổi bật: {product.description}" if product.description else ""
    return (
        f"Dạ {label}, với {product.name}, shop có thể tư vấn theo nhu cầu sử dụng của bạn.{description} "
        "Bạn muốn ưu tiên giá tốt, công dụng, kích cỡ hay thời gian giao hàng ạ?"
    )


def build_shipping_reply(customer_name: str, product: ChatProductContext | None) -> str:
    label = customer_label(customer_name)
    product_note = f" cho {product.name}" if product else ""
    return (
        f"Dạ {label}, shop có hỗ trợ giao hàng{product_note}. "
        "Phí ship và thời gian nhận sẽ phụ thuộc địa chỉ, bạn gửi khu vực nhận hàng để shop kiểm tra nhanh nhé."
    )


def build_stock_reply(customer_name: str, product: ChatProductContext | None) -> str:
    label = customer_label(customer_name)
    if not product:
        return f"Dạ {label}, bạn nhắn giúp tên sản phẩm để shop kiểm tra tồn kho chính xác nhé."
    if product.stock_quantity is None:
        return f"Dạ {label}, shop sẽ kiểm tra tồn kho của {product.name} và phản hồi ngay trong hội thoại này."
    if product.stock_quantity > 0:
        return f"Dạ {label}, {product.name} hiện còn hàng. Bạn có thể nhắn số lượng muốn chốt ngay ạ."
    return f"Dạ {label}, {product.name} hiện tạm hết hàng. Shop có thể tư vấn sản phẩm tương tự nếu bạn muốn."


def build_complaint_reply(customer_name: str) -> str:
    label = customer_label(customer_name)
    return (
        f"Dạ {label}, shop xin lỗi vì trải nghiệm chưa tốt. "
        "Mình đã ghi nhận nội dung này và sẽ chuyển nhân viên phụ trách kiểm tra để hỗ trợ bạn cẩn thận hơn."
    )


def build_default_reply(customer_name: str, product: ChatProductContext | None) -> str:
    label = customer_label(customer_name)
    if product:
        return (
            f"Dạ {label}, shop đang theo dõi tin nhắn của bạn về {product.name}. "
            "Bạn có thể hỏi giá, tồn kho, phí ship hoặc nhắn số lượng muốn mua để shop hỗ trợ ngay."
        )
    return (
        f"Dạ {label}, shop đã nhận được tin nhắn. "
        "Bạn cần hỏi giá, tư vấn sản phẩm, kiểm tra tồn kho hay hỗ trợ đặt hàng ạ?"
    )


def build_chatbot_reply(payload: ChatbotReplyRequest) -> ChatbotReplyResponse:
    normalized_message = normalize_text(payload.message)
    product = choose_product(payload.message, payload.products)
    intent = detect_intent(normalized_message)
    sentiment = detect_sentiment(normalized_message)
    suggested_actions: list[str] = []
    should_escalate = False

    if has_any(normalized_message, PRICE_KEYWORDS):
        intent = "ask_price"
    elif has_any(normalized_message, STOCK_KEYWORDS | SHIPPING_KEYWORDS):
        intent = "consult_request"
    elif has_any(normalized_message, BUYING_KEYWORDS | ORDER_KEYWORDS):
        intent = "buying_intent"

    if has_any(normalized_message, THANKS_KEYWORDS):
        reply = f"Dạ {customer_label(payload.customer_name)}, shop cảm ơn bạn. Khi cần thêm thông tin, bạn cứ nhắn tại đây nhé."
        confidence = 0.76
    elif has_any(normalized_message, HUMAN_HANDOFF_KEYWORDS):
        reply = (
            f"Dạ {customer_label(payload.customer_name)}, mình đã ghi nhận yêu cầu gặp nhân viên. "
            "Shop sẽ chuyển hội thoại này cho nhân viên phụ trách để hỗ trợ trực tiếp."
        )
        should_escalate = True
        confidence = 0.82
        suggested_actions.append("Nhân viên nên tiếp quản hội thoại.")
    elif has_any(normalized_message, SHIPPING_KEYWORDS):
        reply = build_shipping_reply(payload.customer_name, product)
        confidence = 0.82
        suggested_actions.append("Xin địa chỉ nhận hàng để báo phí ship.")
    elif has_any(normalized_message, STOCK_KEYWORDS):
        reply = build_stock_reply(payload.customer_name, product)
        confidence = 0.82
        suggested_actions.append("Kiểm tra tồn kho trước khi chốt đơn.")
    elif intent == "ask_price":
        reply = build_price_reply(payload.customer_name, product)
        confidence = 0.86
        suggested_actions.append("Gửi giá live và hỏi số lượng khách muốn chốt.")
    elif intent == "buying_intent" or has_any(normalized_message, ORDER_KEYWORDS):
        reply = build_buying_reply(payload.customer_name, product)
        confidence = 0.88
        suggested_actions.append("Hỏi số lượng và địa chỉ nhận hàng.")
    elif intent == "complaint" or sentiment == "negative":
        reply = build_complaint_reply(payload.customer_name)
        should_escalate = True
        confidence = 0.84
        suggested_actions.append("Ưu tiên nhân viên xử lý phản hồi tiêu cực.")
    elif intent == "spam":
        reply = "Shop chỉ hỗ trợ thông tin sản phẩm, đơn hàng và giao hàng trong phiên live này ạ."
        confidence = 0.7
        suggested_actions.append("Theo dõi spam nếu khách tiếp tục gửi nội dung không liên quan.")
    elif intent == "consult_request":
        reply = build_consult_reply(payload.customer_name, product)
        confidence = 0.8
        suggested_actions.append("Hỏi thêm nhu cầu để tư vấn sản phẩm.")
    else:
        reply = build_default_reply(payload.customer_name, product)
        confidence = 0.68
        suggested_actions.append("Gợi ý khách chọn nhóm câu hỏi cần hỗ trợ.")

    return ChatbotReplyResponse(
        reply=reply,
        intent=intent,
        sentiment=sentiment,
        confidence=confidence,
        should_escalate=should_escalate,
        suggested_actions=suggested_actions,
        used_product_id=product.product_id if product else None,
    )
