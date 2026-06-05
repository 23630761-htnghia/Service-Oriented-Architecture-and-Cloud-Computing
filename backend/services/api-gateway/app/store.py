from __future__ import annotations

import hashlib
import secrets
from datetime import date, datetime, timezone
from uuid import uuid4

from app.schemas import (
    AILog,
    AutoReplySettings,
    CartItem,
    ChatHistoryItem,
    Livestream,
    Order,
    OrderItem,
    Product,
    SalesPolicy,
    Shop,
    UserPublic,
    UserRecord,
    Voucher,
)

SHOP_ID = "00000000-0000-0000-0000-000000001001"
LIVE_ID = "00000000-0000-0000-0000-000000004001"
PRODUCT_SERUM_ID = "00000000-0000-0000-0000-000000002001"
PRODUCT_LIPSTICK_ID = "00000000-0000-0000-0000-000000002002"
VOUCHER_LIVE20_ID = "00000000-0000-0000-0000-000000003001"

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def public_user(user: UserRecord) -> UserPublic:
    return UserPublic(**user.model_dump(exclude={"password_hash"}))


class RuntimeStore:
    def __init__(self) -> None:
        self.users: dict[str, UserRecord] = {}
        self.sessions: dict[str, str] = {}
        self.shops: dict[str, Shop] = {}
        self.livestreams: dict[str, Livestream] = {}
        self.livestream_products: dict[str, list[str]] = {}
        self.products: dict[str, Product] = {}
        self.vouchers: dict[str, Voucher] = {}
        self.policies: dict[str, SalesPolicy] = {}
        self.settings = AutoReplySettings(enabled=True)
        self.chat_history: list[ChatHistoryItem] = []
        self.ai_logs: list[AILog] = []
        self.carts: dict[str, list[CartItem]] = {}
        self.orders: list[Order] = []
        self._seed()

    def _seed_user(self, user_id: str, full_name: str, email: str, role: str) -> None:
        self.users[user_id] = UserRecord(
            id=user_id,
            full_name=full_name,
            email=email.lower(),
            password_hash=hash_password("123456"),
            role=role,  # type: ignore[arg-type]
            status="ACTIVE",
            created_at=now_iso(),
        )

    def _seed(self) -> None:
        self._seed_user("customer-01", "Khách hàng Mẫu", "customer@smartlive.test", "CUSTOMER")
        self._seed_user("seller-01", "Người bán Mẫu", "seller@smartlive.test", "SELLER")
        self._seed_user("admin-01", "Admin Mẫu", "admin@smartlive.test", "ADMIN")

        self.shops[SHOP_ID] = Shop(
            id=SHOP_ID,
            seller_id="seller-01",
            name="SmartLive Beauty & Home",
            description="Shop mẫu bán mỹ phẩm, thiết bị nhỏ và đồ gia dụng trong livestream.",
            logo_url=None,
            created_at=now_iso(),
        )
        self.livestreams[LIVE_ID] = Livestream(
            id=LIVE_ID,
            shop_id=SHOP_ID,
            title="Flash sale tối nay",
            description="AI tư vấn tự động trong khung chat livestream.",
            status="LIVE",
            ai_enabled=True,
            started_at=now_iso(),
            viewer_count=1284,
        )
        self.products = {
            PRODUCT_SERUM_ID: Product(
                product_id=PRODUCT_SERUM_ID,
                shop_id=SHOP_ID,
                name="Serum Vitamin C Glow",
                description="Serum dưỡng sáng da, phù hợp tư vấn trong livestream.",
                category="Skincare",
                brand="LumiSkin",
                retail_price=199000,
                live_price=129000,
                stock_quantity=25,
                variants=["30ml", "50ml"],
                image_url="https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=900&q=80",
                purchase_url="https://shop.example.com/serum-vitamin-c",
                related_product_ids=[PRODUCT_LIPSTICK_ID],
            ),
            PRODUCT_LIPSTICK_ID: Product(
                product_id=PRODUCT_LIPSTICK_ID,
                shop_id=SHOP_ID,
                name="Son Kem Velvet Rose",
                description="Son kem lì màu hồng đất, chất son nhẹ môi.",
                category="Makeup",
                brand="Velvet",
                retail_price=159000,
                live_price=99000,
                stock_quantity=40,
                variants=["Rose", "Coral", "Nude"],
                image_url="https://images.unsplash.com/photo-1584017911766-d451b3d0e843?auto=format&fit=crop&w=900&q=80",
                purchase_url="https://shop.example.com/velvet-rose",
            ),
        }
        self.livestream_products[LIVE_ID] = list(self.products.keys())
        self.vouchers = {
            VOUCHER_LIVE20_ID: Voucher(
                voucher_id=VOUCHER_LIVE20_ID,
                shop_id=SHOP_ID,
                code="LIVE20",
                discount_type="PERCENT",
                discount_value="giảm 20%",
                min_order_value=150000,
                conditions="áp dụng cho đơn từ 150.000đ",
                start_date="2026-06-01",
                valid_until="2026-06-30",
                applicable_product_ids=[],
                remaining_quantity=100,
            ),
        }
        self.policies[SHOP_ID] = SalesPolicy(
            shop_id=SHOP_ID,
            shipping_fee_note="Phí ship nội thành từ 20.000đ, miễn phí ship cho đơn từ 399.000đ.",
            delivery_time_note="Thời gian giao dự kiến 1-2 ngày ở nội thành và 3-5 ngày ở tỉnh.",
            return_policy="Đổi trả trong 7 ngày nếu sản phẩm lỗi từ nhà sản xuất, còn tem và hóa đơn mua hàng.",
            warranty_policy="Bảo hành theo chính sách từng sản phẩm được công bố trong livestream.",
        )

    def create_session(self, user_id: str) -> str:
        token = secrets.token_urlsafe(32)
        self.sessions[token] = user_id
        return token

    def user_by_token(self, token: str) -> UserRecord | None:
        user_id = self.sessions.get(token)
        return self.users.get(user_id) if user_id else None

    def user_by_email(self, email: str) -> UserRecord | None:
        normalized = email.lower()
        return next((user for user in self.users.values() if user.email == normalized), None)

    def register_user(self, full_name: str, email: str, password: str, role: str) -> UserRecord:
        if self.user_by_email(email):
            raise ValueError("Email already exists")
        user_id = f"{role.lower()}-{uuid4().hex[:8]}"
        user = UserRecord(
            id=user_id,
            full_name=full_name,
            email=email.lower(),
            password_hash=hash_password(password),
            role=role,  # type: ignore[arg-type]
            status="ACTIVE",
            created_at=now_iso(),
        )
        self.users[user_id] = user
        if role == "SELLER":
            shop_id = f"shop-{uuid4().hex[:8]}"
            self.shops[shop_id] = Shop(
                id=shop_id,
                seller_id=user_id,
                name=f"Shop của {full_name}",
                description="Shop mới trên SmartLive.",
                logo_url=None,
                created_at=now_iso(),
            )
        return user

    def seller_shop(self, seller_id: str) -> Shop | None:
        return next((shop for shop in self.shops.values() if shop.seller_id == seller_id), None)

    def shop_for_livestream(self, livestream_id: str) -> Shop | None:
        livestream = self.livestreams.get(livestream_id)
        return self.shops.get(livestream.shop_id) if livestream else None

    def user_can_manage_shop(self, user: UserRecord, shop_id: str) -> bool:
        if user.role == "ADMIN":
            return True
        shop = self.shops.get(shop_id)
        return bool(shop and shop.seller_id == user.id)

    def products_for_livestream(self, livestream_id: str) -> list[Product]:
        product_ids = self.livestream_products.get(livestream_id, [])
        return [product for product_id in product_ids if (product := self.products.get(product_id))]

    def vouchers_for_shop(self, shop_id: str) -> list[Voucher]:
        today = date.today().isoformat()
        return [
            voucher
            for voucher in self.vouchers.values()
            if voucher.shop_id == shop_id
            and voucher.status == "ACTIVE"
            and voucher.remaining_quantity > 0
            and (not voucher.start_date or voucher.start_date <= today)
            and (not voucher.valid_until or voucher.valid_until >= today)
        ]

    def upsert_product(self, product: Product) -> Product:
        self.products[product.product_id] = product
        if product.product_id not in self.livestream_products.get(LIVE_ID, []):
            self.livestream_products.setdefault(LIVE_ID, []).append(product.product_id)
        return product

    def delete_product(self, product_id: str) -> bool:
        deleted = self.products.pop(product_id, None) is not None
        for product_ids in self.livestream_products.values():
            if product_id in product_ids:
                product_ids.remove(product_id)
        return deleted

    def upsert_voucher(self, voucher: Voucher) -> Voucher:
        self.vouchers[voucher.voucher_id] = voucher
        return voucher

    def delete_voucher(self, voucher_id: str) -> bool:
        return self.vouchers.pop(voucher_id, None) is not None

    def add_chat(
        self,
        livestream_id: str,
        user_id: str | None,
        customer_name: str | None,
        message: str,
        sender_type: str,
        source_platform: str,
        ai_reply: str | None = None,
        intent: str | None = None,
        confidence_score: float | None = None,
        should_escalate: bool = False,
    ) -> ChatHistoryItem:
        status = "NEED_SELLER_SUPPORT" if should_escalate else ("ANSWERED" if ai_reply else None)
        chat = ChatHistoryItem(
            chat_id=str(uuid4()),
            livestream_id=livestream_id,
            user_id=user_id,
            customer_name=customer_name,
            message=message,
            sender_type=sender_type,  # type: ignore[arg-type]
            ai_reply=ai_reply,
            intent=intent,
            confidence_score=confidence_score,
            ai_status=status,  # type: ignore[arg-type]
            should_escalate=should_escalate,
            source_platform=source_platform,
            created_at=now_iso(),
        )
        self.chat_history.append(chat)
        return chat

    def add_ai_log(
        self,
        livestream_id: str,
        customer_message_id: str,
        ai_message_id: str | None,
        confidence_score: float,
        status: str,
        question_type: str | None = None,
        retrieved_context: dict | None = None,
        prompt: str | None = None,
        raw_model_response: str | None = None,
        final_reply: str | None = None,
        error_message: str | None = None,
    ) -> AILog:
        log = AILog(
            id=str(uuid4()),
            livestream_id=livestream_id,
            customer_message_id=customer_message_id,
            ai_message_id=ai_message_id,
            question_type=question_type,
            retrieved_context=retrieved_context,
            prompt=prompt,
            raw_model_response=raw_model_response,
            final_reply=final_reply,
            confidence_score=confidence_score,
            status=status,  # type: ignore[arg-type]
            error_message=error_message,
            created_at=now_iso(),
        )
        self.ai_logs.append(log)
        return log

    def create_order(self, customer_id: str, items: list[CartItem]) -> Order:
        order_items: list[OrderItem] = []
        shop_id = SHOP_ID
        for item in items:
            product = self.products[item.product_id]
            shop_id = product.shop_id
            order_items.append(
                OrderItem(
                    product_id=product.product_id,
                    quantity=item.quantity,
                    price=product.live_price or product.retail_price,
                )
            )
        total = sum(item.price * item.quantity for item in order_items)
        order = Order(
            id=f"order-{uuid4().hex[:8]}",
            customer_id=customer_id,
            shop_id=shop_id,
            total_amount=total,
            status="PENDING",
            items=order_items,
            created_at=now_iso(),
        )
        self.orders.append(order)
        self.carts[customer_id] = []
        return order


store = RuntimeStore()
