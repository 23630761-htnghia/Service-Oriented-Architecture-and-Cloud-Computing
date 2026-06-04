from __future__ import annotations

import httpx
import time
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas import (
    AuthResponse,
    AutoReplySettings,
    CartItem,
    CartItemRequest,
    CreateOrderRequest,
    GatewayHealthResponse,
    Livestream,
    LivestreamInput,
    LivestreamMessageRequest,
    LivestreamMessageResponse,
    LoginRequest,
    ManualReplyRequest,
    Product,
    RegisterRequest,
    RoleUpdateRequest,
    SalesPolicy,
    Shop,
    StatusUpdateRequest,
    UserPublic,
    Voucher,
)
from app.store import hash_password, public_user, store


app = FastAPI(
    title="SmartLive Intelligent Livestream API Gateway",
    version="2.0.0",
    description="RBAC, livestream chat, seller dashboard, admin dashboard and AI auto-reply gateway.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

request_counters: dict[str, list[float]] = {}
total_requests = 0


class RealtimeHub:
    def __init__(self) -> None:
        self.rooms: dict[str, list[WebSocket]] = {}

    async def connect(self, livestream_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.rooms.setdefault(livestream_id, []).append(websocket)

    def disconnect(self, livestream_id: str, websocket: WebSocket) -> None:
        sockets = self.rooms.get(livestream_id, [])
        if websocket in sockets:
            sockets.remove(websocket)

    async def broadcast(self, livestream_id: str, event: str, payload: dict) -> None:
        for socket in list(self.rooms.get(livestream_id, [])):
            try:
                await socket.send_json({"event": event, "payload": payload})
            except RuntimeError:
                self.disconnect(livestream_id, socket)


hub = RealtimeHub()


async def forward_post(base_url: str, path: str, payload: dict):
    response = await app.state.client.post(f"{base_url}{path}", json=payload)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


async def forward_request(base_url: str, path: str, method: str, payload: dict | None = None):
    response = await app.state.client.request(method, f"{base_url.rstrip('/')}/{path.lstrip('/')}", json=payload)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    try:
        return response.json()
    except ValueError:
        return {"status": response.status_code, "body": response.text}


async def check_ai_service() -> dict:
    try:
        response = await app.state.client.get(f"{settings.ai_service_url}/health")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError:
        return {"status": "unreachable", "service": "ai-assistant-service"}


def service_registry() -> dict[str, str]:
    return {
        "auth-service": settings.auth_service_url,
        "user-service": settings.user_service_url,
        "shop-service": settings.shop_service_url,
        "product-service": settings.product_service_url,
        "voucher-service": settings.voucher_service_url,
        "livestream-service": settings.livestream_service_url,
        "chat-service": settings.chat_service_url,
        "ai-assistant-service": settings.ai_service_url,
        "order-service": settings.order_service_url,
        "notification-service": settings.notification_service_url,
        "analytics-service": settings.analytics_service_url,
    }


@app.middleware("http")
async def request_logging_and_rate_limit(request: Request, call_next):
    global total_requests
    client = request.client.host if request.client else "unknown"
    now = time.time()
    window = [timestamp for timestamp in request_counters.get(client, []) if now - timestamp < 60]
    if len(window) >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    window.append(now)
    request_counters[client] = window
    total_requests += 1
    start = time.time()
    response = await call_next(request)
    response.headers["X-Gateway-Service"] = "api-gateway"
    response.headers["X-Request-Duration-Ms"] = str(round((time.time() - start) * 1000, 2))
    return response


def current_user(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    user = store.user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    if user.status != "ACTIVE":
        raise HTTPException(status_code=403, detail="Account is locked")
    return user


def require_roles(*roles: str):
    def dependency(user=Depends(current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Require role: {', '.join(roles)}")
        return user

    return dependency


def require_seller_shop(user) -> Shop:
    shop = store.seller_shop(user.id)
    if not shop:
        raise HTTPException(status_code=404, detail="Seller shop not found")
    return shop


def assert_can_manage_shop(user, shop_id: str) -> None:
    if not store.user_can_manage_shop(user, shop_id):
        raise HTTPException(status_code=403, detail="You can only manage data in your own shop")


@app.on_event("startup")
async def startup_event():
    app.state.client = httpx.AsyncClient(timeout=10.0)


@app.on_event("shutdown")
async def shutdown_event():
    await app.state.client.aclose()


@app.get("/")
async def root():
    return {
        "service": "api-gateway",
        "status": "ok",
        "message": "SmartLive intelligent livestream API is running.",
        "demo_accounts": {
            "CUSTOMER": "customer@smartlive.test / 123456",
            "SELLER": "seller@smartlive.test / 123456",
            "ADMIN": "admin@smartlive.test / 123456",
        },
    }


@app.get("/health", response_model=GatewayHealthResponse)
async def health_check():
    return GatewayHealthResponse(
        status="ok",
        service="api-gateway",
        dependencies={"ai_service": await check_ai_service()},
    )


@app.get("/ready")
async def readiness_check():
    return {"status": "ready", "service": "api-gateway", "registry": service_registry()}


@app.get("/service-registry")
async def get_service_registry():
    return service_registry()


@app.api_route("/services/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def service_proxy(service_name: str, path: str, request: Request, user=Depends(current_user)):
    registry = service_registry()
    base_url = registry.get(service_name)
    if not base_url:
        raise HTTPException(status_code=404, detail="Unknown service")
    payload = None
    if request.method in {"POST", "PUT", "PATCH"}:
        try:
            payload = await request.json()
        except ValueError:
            payload = {}
    return await forward_request(base_url, path, request.method, payload)


@app.get("/metrics")
async def metrics():
    body = (
        "# HELP smartlive_gateway_requests_total Total HTTP requests handled by API Gateway\n"
        "# TYPE smartlive_gateway_requests_total counter\n"
        f"smartlive_gateway_requests_total {total_requests}\n"
        "# HELP smartlive_gateway_clients_active Number of clients seen in the current process\n"
        "# TYPE smartlive_gateway_clients_active gauge\n"
        f"smartlive_gateway_clients_active {len(request_counters)}\n"
    )
    return Response(content=body, media_type="text/plain")


@app.post("/auth/register", response_model=AuthResponse)
async def register(payload: RegisterRequest):
    try:
        user = store.register_user(payload.full_name, payload.email, payload.password, payload.role)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    token = store.create_session(user.id)
    return AuthResponse(access_token=token, user=public_user(user))


@app.post("/auth/login", response_model=AuthResponse)
async def login(payload: LoginRequest):
    user = store.user_by_email(payload.email)
    if not user or user.password_hash != hash_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.status != "ACTIVE":
        raise HTTPException(status_code=403, detail="Account is locked")
    token = store.create_session(user.id)
    return AuthResponse(access_token=token, user=public_user(user))


@app.get("/auth/me", response_model=UserPublic)
async def me(user=Depends(current_user)):
    return public_user(user)


@app.get("/livestreams", response_model=list[Livestream])
async def list_livestreams(user=Depends(require_roles("CUSTOMER", "SELLER", "ADMIN"))):
    if user.role == "SELLER":
        shop = require_seller_shop(user)
        return [live for live in store.livestreams.values() if live.shop_id == shop.id]
    return list(store.livestreams.values())


@app.get("/livestreams/{livestream_id}", response_model=Livestream)
async def get_livestream(livestream_id: str, user=Depends(require_roles("CUSTOMER", "SELLER", "ADMIN"))):
    livestream = store.livestreams.get(livestream_id)
    if not livestream:
        raise HTTPException(status_code=404, detail="Livestream not found")
    if user.role == "SELLER":
        assert_can_manage_shop(user, livestream.shop_id)
    return livestream


@app.get("/livestreams/{livestream_id}/products", response_model=list[Product])
async def livestream_products(livestream_id: str, user=Depends(require_roles("CUSTOMER", "SELLER", "ADMIN"))):
    livestream = store.livestreams.get(livestream_id)
    if not livestream:
        raise HTTPException(status_code=404, detail="Livestream not found")
    if user.role == "SELLER":
        assert_can_manage_shop(user, livestream.shop_id)
    return store.products_for_livestream(livestream_id)


@app.post("/livestreams/{livestream_id}/chat", response_model=LivestreamMessageResponse)
async def livestream_chat(
    livestream_id: str,
    payload: LivestreamMessageRequest,
    user=Depends(require_roles("CUSTOMER", "SELLER", "ADMIN")),
):
    payload.livestream_id = livestream_id
    return await handle_livestream_message(payload, user)


async def handle_livestream_message(payload: LivestreamMessageRequest, user) -> LivestreamMessageResponse:
    livestream = store.livestreams.get(payload.livestream_id)
    if not livestream:
        raise HTTPException(status_code=404, detail="Livestream not found")
    shop = store.shops[livestream.shop_id]

    chat = store.add_chat(
        livestream_id=payload.livestream_id,
        user_id=user.id if user else None,
        customer_name=payload.customer_name or getattr(user, "full_name", None),
        message=payload.message,
        sender_type=getattr(user, "role", "CUSTOMER") if getattr(user, "role", "CUSTOMER") in {"CUSTOMER", "SELLER"} else "CUSTOMER",
        source_platform=payload.source_platform,
    )
    await hub.broadcast(payload.livestream_id, "customer_message", chat.model_dump())

    ai_reply = None
    intent = None
    confidence = None
    should_escalate = False
    if livestream.ai_enabled and store.settings.enabled and store.settings.auto_reply_enabled:
        await hub.broadcast(payload.livestream_id, "ai_processing", {"customer_message_id": chat.chat_id})
        products = store.products_for_livestream(payload.livestream_id)
        selected = store.products.get(payload.product_id) if payload.product_id else None
        if selected:
            products = [selected, *[product for product in products if product.product_id != selected.product_id]]

        response = await forward_post(
            settings.ai_service_url,
            "/chatbot/reply",
            {
                "message": payload.message,
                "customer_name": payload.customer_name or getattr(user, "full_name", None),
                "account_name": shop.name,
                "products": [product.model_dump() for product in products],
                "vouchers": [voucher.model_dump() for voucher in store.vouchers_for_shop(shop.id)],
                "policy": store.policies.get(shop.id, SalesPolicy(shop_id=shop.id)).model_dump(),
                "ai_settings": {
                    "model_name": store.settings.model_name,
                    "temperature": store.settings.temperature,
                    "max_tokens": store.settings.max_tokens,
                    "reply_style": store.settings.reply_style,
                },
                "conversation_history": [
                    {
                        "sender_role": item.sender_type.lower(),
                        "sender_name": item.customer_name,
                        "content": item.message,
                        "source": item.source_platform,
                        "created_at": item.created_at,
                    }
                    for item in store.chat_history[-12:]
                ],
            },
        )
        ai_reply = response.get("reply")
        intent = response.get("intent")
        confidence = response.get("confidence")
        should_escalate = bool(response.get("should_escalate"))
        chat.ai_reply = ai_reply
        chat.intent = intent
        chat.confidence_score = confidence
        chat.should_escalate = should_escalate
        chat.ai_status = "NEED_SELLER_SUPPORT" if should_escalate else "ANSWERED"
        ai_message_id = None
        if ai_reply:
            ai_message = store.add_chat(
                livestream_id=payload.livestream_id,
                user_id=None,
                customer_name="SmartLive AI",
                message=ai_reply,
                sender_type="AI",
                source_platform="ai-assistant-service",
            )
            ai_message_id = ai_message.chat_id
            await hub.broadcast(payload.livestream_id, "ai_reply", ai_message.model_dump())
        if should_escalate:
            await hub.broadcast(payload.livestream_id, "need_seller_support", chat.model_dump())
        store.add_ai_log(
            payload.livestream_id,
            chat.chat_id,
            ai_message_id,
            float(confidence or 0),
            response.get("ai_status") or ("NEED_SELLER_SUPPORT" if should_escalate else "ANSWERED"),
            question_type=intent,
            retrieved_context=response.get("retrieved_context"),
            prompt=response.get("prompt"),
            raw_model_response=response.get("raw_model_response"),
            final_reply=ai_reply,
            error_message=response.get("error_message"),
        )

    return LivestreamMessageResponse(chat=chat, auto_reply_enabled=livestream.ai_enabled and store.settings.enabled)


@app.websocket("/ws/livestreams/{livestream_id}")
async def livestream_socket(websocket: WebSocket, livestream_id: str, token: str | None = None):
    user = store.user_by_token(token or "")
    if not user:
        await websocket.close(code=1008)
        return
    await hub.connect(livestream_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            event = data.get("event")
            payload = data.get("payload") or {}
            if event == "customer_message":
                response = await handle_livestream_message(
                    LivestreamMessageRequest(
                        livestream_id=livestream_id,
                        customer_name=user.full_name,
                        message=payload.get("message", ""),
                        product_id=payload.get("product_id"),
                        source_platform="websocket",
                    ),
                    user,
                )
                await websocket.send_json({"event": "message_saved", "payload": response.model_dump()})
            elif event == "seller_reply" and user.role in {"SELLER", "ADMIN"}:
                livestream = store.livestreams.get(livestream_id)
                if livestream and user.role == "SELLER":
                    assert_can_manage_shop(user, livestream.shop_id)
                chat = store.add_chat(
                    livestream_id=livestream_id,
                    user_id=user.id,
                    customer_name=user.full_name,
                    message=payload.get("message", ""),
                    sender_type="SELLER",
                    source_platform="websocket",
                )
                await hub.broadcast(livestream_id, "seller_reply", chat.model_dump())
            elif event == "product_pinned" and user.role in {"SELLER", "ADMIN"}:
                await hub.broadcast(livestream_id, "product_pinned", payload)
    except WebSocketDisconnect:
        hub.disconnect(livestream_id, websocket)


@app.post("/cart/items", response_model=list[CartItem])
async def add_cart_item(payload: CartItemRequest, user=Depends(require_roles("CUSTOMER"))):
    if payload.product_id not in store.products:
        raise HTTPException(status_code=404, detail="Product not found")
    cart = store.carts.setdefault(user.id, [])
    existing = next((item for item in cart if item.product_id == payload.product_id), None)
    if existing:
        existing.quantity += payload.quantity
    else:
        cart.append(CartItem(product_id=payload.product_id, quantity=payload.quantity))
    return cart


@app.post("/orders")
async def create_order(payload: CreateOrderRequest, user=Depends(require_roles("CUSTOMER"))):
    items = [CartItem(product_id=item.product_id, quantity=item.quantity) for item in payload.items]
    if not items:
        items = store.carts.get(user.id, [])
    if not items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    for item in items:
        if item.product_id not in store.products:
            raise HTTPException(status_code=404, detail=f"Product not found: {item.product_id}")
    return store.create_order(user.id, items)


@app.get("/orders/me")
async def my_orders(user=Depends(require_roles("CUSTOMER"))):
    return [order for order in store.orders if order.customer_id == user.id]


@app.post("/seller/livestreams", response_model=Livestream)
async def seller_create_livestream(payload: LivestreamInput, user=Depends(require_roles("SELLER"))):
    shop = require_seller_shop(user)
    livestream = Livestream(
        id=f"live-{len(store.livestreams) + 1:02d}",
        shop_id=shop.id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        ai_enabled=payload.ai_enabled,
        started_at=None,
        viewer_count=0,
    )
    store.livestreams[livestream.id] = livestream
    store.livestream_products.setdefault(livestream.id, [])
    return livestream


@app.put("/seller/livestreams/{livestream_id}", response_model=Livestream)
async def seller_update_livestream(livestream_id: str, payload: LivestreamInput, user=Depends(require_roles("SELLER"))):
    livestream = store.livestreams.get(livestream_id)
    if not livestream:
        raise HTTPException(status_code=404, detail="Livestream not found")
    assert_can_manage_shop(user, livestream.shop_id)
    livestream.title = payload.title
    livestream.description = payload.description
    livestream.status = payload.status
    livestream.ai_enabled = payload.ai_enabled
    return livestream


@app.delete("/seller/livestreams/{livestream_id}")
async def seller_delete_livestream(livestream_id: str, user=Depends(require_roles("SELLER"))):
    livestream = store.livestreams.get(livestream_id)
    if not livestream:
        raise HTTPException(status_code=404, detail="Livestream not found")
    assert_can_manage_shop(user, livestream.shop_id)
    del store.livestreams[livestream_id]
    return {"deleted": True}


@app.post("/seller/products", response_model=Product)
async def seller_create_product(product: Product, user=Depends(require_roles("SELLER"))):
    shop = require_seller_shop(user)
    product.shop_id = shop.id
    return store.upsert_product(product)


@app.put("/seller/products/{product_id}", response_model=Product)
async def seller_update_product(product_id: str, product: Product, user=Depends(require_roles("SELLER"))):
    existing = store.products.get(product_id)
    if existing:
        assert_can_manage_shop(user, existing.shop_id)
    shop = require_seller_shop(user)
    product.product_id = product_id
    product.shop_id = shop.id
    return store.upsert_product(product)


@app.delete("/seller/products/{product_id}")
async def seller_delete_product(product_id: str, user=Depends(require_roles("SELLER"))):
    product = store.products.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    assert_can_manage_shop(user, product.shop_id)
    return {"deleted": store.delete_product(product_id)}


@app.post("/seller/vouchers", response_model=Voucher)
async def seller_create_voucher(voucher: Voucher, user=Depends(require_roles("SELLER"))):
    shop = require_seller_shop(user)
    voucher.shop_id = shop.id
    return store.upsert_voucher(voucher)


@app.get("/seller/vouchers", response_model=list[Voucher])
async def seller_list_vouchers(user=Depends(require_roles("SELLER"))):
    shop = require_seller_shop(user)
    return [voucher for voucher in store.vouchers.values() if voucher.shop_id == shop.id]


@app.put("/seller/vouchers/{voucher_id}", response_model=Voucher)
async def seller_update_voucher(voucher_id: str, voucher: Voucher, user=Depends(require_roles("SELLER"))):
    existing = store.vouchers.get(voucher_id)
    if existing:
        assert_can_manage_shop(user, existing.shop_id)
    shop = require_seller_shop(user)
    voucher.voucher_id = voucher_id
    voucher.shop_id = shop.id
    return store.upsert_voucher(voucher)


@app.delete("/seller/vouchers/{voucher_id}")
async def seller_delete_voucher(voucher_id: str, user=Depends(require_roles("SELLER"))):
    voucher = store.vouchers.get(voucher_id)
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    assert_can_manage_shop(user, voucher.shop_id)
    return {"deleted": store.delete_voucher(voucher_id)}


@app.patch("/seller/livestreams/{livestream_id}/ai-toggle", response_model=Livestream)
async def seller_toggle_ai(livestream_id: str, payload: AutoReplySettings, user=Depends(require_roles("SELLER"))):
    livestream = store.livestreams.get(livestream_id)
    if not livestream:
        raise HTTPException(status_code=404, detail="Livestream not found")
    assert_can_manage_shop(user, livestream.shop_id)
    livestream.ai_enabled = payload.enabled
    store.settings = payload
    return livestream


@app.get("/seller/livestreams/{livestream_id}/questions")
async def seller_questions(livestream_id: str, user=Depends(require_roles("SELLER"))):
    livestream = store.livestreams.get(livestream_id)
    if not livestream:
        raise HTTPException(status_code=404, detail="Livestream not found")
    assert_can_manage_shop(user, livestream.shop_id)
    return [chat for chat in store.chat_history if chat.livestream_id == livestream_id and chat.sender_type == "CUSTOMER"]


@app.get("/seller/livestreams/{livestream_id}/ai-fallbacks")
async def seller_ai_fallbacks(livestream_id: str, user=Depends(require_roles("SELLER"))):
    livestream = store.livestreams.get(livestream_id)
    if not livestream:
        raise HTTPException(status_code=404, detail="Livestream not found")
    assert_can_manage_shop(user, livestream.shop_id)
    return [chat for chat in store.chat_history if chat.livestream_id == livestream_id and chat.should_escalate]


@app.get("/seller/livestreams/{livestream_id}/ai-logs")
async def seller_ai_logs(livestream_id: str, user=Depends(require_roles("SELLER"))):
    livestream = store.livestreams.get(livestream_id)
    if not livestream:
        raise HTTPException(status_code=404, detail="Livestream not found")
    assert_can_manage_shop(user, livestream.shop_id)
    return [log for log in store.ai_logs if log.livestream_id == livestream_id]


@app.put("/seller/ai-settings", response_model=AutoReplySettings)
async def seller_update_ai_settings(payload: AutoReplySettings, user=Depends(require_roles("SELLER"))):
    require_seller_shop(user)
    store.settings = payload
    return store.settings


@app.post("/seller/livestreams/{livestream_id}/manual-reply")
async def seller_manual_reply(livestream_id: str, payload: ManualReplyRequest, user=Depends(require_roles("SELLER"))):
    livestream = store.livestreams.get(livestream_id)
    if not livestream:
        raise HTTPException(status_code=404, detail="Livestream not found")
    assert_can_manage_shop(user, livestream.shop_id)
    chat = store.add_chat(
        livestream_id=livestream_id,
        user_id=user.id,
        customer_name=user.full_name,
        message=payload.message,
        sender_type="SELLER",
        source_platform="manual",
    )
    await hub.broadcast(livestream_id, "seller_reply", chat.model_dump())
    return chat


@app.get("/seller/analytics")
async def seller_analytics(user=Depends(require_roles("SELLER"))):
    shop = require_seller_shop(user)
    livestream_ids = [live.id for live in store.livestreams.values() if live.shop_id == shop.id]
    orders = [order for order in store.orders if order.shop_id == shop.id]
    return {
        "viewer_count": sum(store.livestreams[live_id].viewer_count for live_id in livestream_ids),
        "question_count": sum(1 for chat in store.chat_history if chat.livestream_id in livestream_ids and chat.sender_type == "CUSTOMER"),
        "fallback_count": sum(1 for chat in store.chat_history if chat.livestream_id in livestream_ids and chat.should_escalate),
        "order_count": len(orders),
        "revenue": sum(order.total_amount for order in orders),
    }


@app.put("/seller/policy", response_model=SalesPolicy)
async def seller_update_policy(policy: SalesPolicy, user=Depends(require_roles("SELLER"))):
    shop = require_seller_shop(user)
    policy.shop_id = shop.id
    store.policies[shop.id] = policy
    return policy


@app.get("/admin/users", response_model=list[UserPublic])
async def admin_users(user=Depends(require_roles("ADMIN"))):
    return [public_user(item) for item in store.users.values()]


@app.patch("/admin/users/{user_id}/role", response_model=UserPublic)
async def admin_update_role(user_id: str, payload: RoleUpdateRequest, user=Depends(require_roles("ADMIN"))):
    target = store.users.get(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.role = payload.role
    return public_user(target)


@app.patch("/admin/users/{user_id}/status", response_model=UserPublic)
async def admin_update_status(user_id: str, payload: StatusUpdateRequest, user=Depends(require_roles("ADMIN"))):
    target = store.users.get(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.status = payload.status
    return public_user(target)


@app.get("/admin/shops")
async def admin_shops(user=Depends(require_roles("ADMIN"))):
    return list(store.shops.values())


@app.get("/admin/livestreams")
async def admin_livestreams(user=Depends(require_roles("ADMIN"))):
    return list(store.livestreams.values())


@app.get("/admin/orders")
async def admin_orders(user=Depends(require_roles("ADMIN"))):
    return store.orders


@app.get("/admin/ai-logs")
async def admin_ai_logs(user=Depends(require_roles("ADMIN"))):
    return store.ai_logs
