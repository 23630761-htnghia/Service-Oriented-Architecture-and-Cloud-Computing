from __future__ import annotations

from datetime import datetime
import os
import re
from uuid import uuid4

import httpx
from fastapi import FastAPI, HTTPException

from app.database import delete_json_record, get_connection, initialize_database, save_json_record
from app.schemas import (
    AiAssistantSettings,
    AiAssistantSettingsUpdate,
    CartItemCreateRequest,
    CartItemResponse,
    CartMutationResponse,
    CheckoutResponse,
    CustomerOrder,
    CustomerOrderItem,
    CustomerProfile,
    CustomerRegisterRequest,
    LivestreamComment,
    LivestreamCommentCreateRequest,
    LivestreamCommentCreateResponse,
    LivestreamMessage,
    LivestreamMessageCreateRequest,
    DemoLoginRequest,
    DemoLoginResponse,
    DemoUserProfile,
    HealthResponse,
    ManagedUserCreate,
    StaffUserCreate,
    UserAccount,
    UserDeleteResponse,
    UserPasswordUpdate,
)

app = FastAPI(
    title="Identity Service",
    version="0.4.0",
    description="Identity and internal user management service for livestream management.",
)

MANAGED_USER_ROLES = {"staff", "product_manager"}
STAFF_REPLY_ROLES = {"admin", "staff"}
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001")


@app.on_event("startup")
def startup_event() -> None:
    initialize_database()


def fetch_all(query: str, params: tuple = ()) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def fetch_one(query: str, params: tuple = ()) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(query, params).fetchone()
    return dict(row) if row else None


def get_current_timestamp(connection) -> str:
    return connection.execute("SELECT datetime('now')").fetchone()[0]


def normalize_staff_code(staff_code: str) -> str:
    normalized_code = re.sub(r"[^A-Z0-9-]", "", staff_code.strip().upper())
    if len(normalized_code) < 2:
        raise HTTPException(status_code=400, detail="Mã staff phải có ít nhất 2 ký tự hợp lệ.")
    return normalized_code


def validate_managed_role(role: str) -> str:
    normalized_role = role.strip().lower()
    if normalized_role not in MANAGED_USER_ROLES:
        raise HTTPException(status_code=400, detail="Vai trò quản lý không hợp lệ.")
    return normalized_role


def build_managed_user_id(staff_code: str) -> str:
    return f"user-{staff_code.lower()}"


def get_user_record(user_id: str) -> dict:
    user = fetch_one(
        """
        SELECT user_id, staff_code, email, password, full_name, role, phone, department, status, created_at, last_login_at
        FROM users
        WHERE user_id = ?
        """,
        (user_id,),
    )
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản trong hệ thống.")
    return user


def require_managed_user(user_id: str) -> dict:
    user = get_user_record(user_id)
    if user["role"] not in MANAGED_USER_ROLES:
        raise HTTPException(status_code=400, detail="Chỉ có thể thao tác trên tài khoản nội bộ.")
    return user


def build_managed_user_record(user_id: str, payload: ManagedUserCreate, created_at: str) -> dict:
    return {
        "user_id": user_id,
        "staff_code": normalize_staff_code(payload.staff_code),
        "email": payload.email.strip().lower(),
        "password": payload.password,
        "full_name": payload.full_name.strip(),
        "role": validate_managed_role(payload.role),
        "phone": payload.phone.strip(),
        "department": payload.department.strip(),
        "status": payload.status,
        "created_at": created_at,
        "last_login_at": None,
    }


def create_managed_user_account(payload: ManagedUserCreate) -> UserAccount:
    normalized_staff_code = normalize_staff_code(payload.staff_code)
    user_id = build_managed_user_id(normalized_staff_code)
    normalized_email = payload.email.strip().lower()

    if fetch_one("SELECT user_id FROM users WHERE staff_code = ?", (normalized_staff_code,)):
        raise HTTPException(status_code=409, detail="Mã nội bộ đã tồn tại. Hãy xóa tài khoản cũ trước khi tạo lại.")
    if fetch_one("SELECT user_id FROM users WHERE email = ?", (normalized_email,)):
        raise HTTPException(status_code=409, detail="Email này đã tồn tại trong hệ thống.")
    if fetch_one("SELECT user_id FROM users WHERE user_id = ?", (user_id,)):
        raise HTTPException(status_code=409, detail="Mã nội bộ này đang xung đột với tài khoản khác trong hệ thống.")

    with get_connection() as connection:
        created_at = get_current_timestamp(connection)
        record = build_managed_user_record(user_id, payload, created_at)
        connection.execute(
            """
            INSERT INTO users (
                user_id,
                staff_code,
                email,
                password,
                full_name,
                role,
                phone,
                department,
                status,
                created_at,
                last_login_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(
                record[column]
                for column in [
                    "user_id",
                    "staff_code",
                    "email",
                    "password",
                    "full_name",
                    "role",
                    "phone",
                    "department",
                    "status",
                    "created_at",
                    "last_login_at",
                ]
            ),
        )
        connection.commit()

    save_json_record("users", record)
    return UserAccount(**record)


def list_users_data() -> list[UserAccount]:
    rows = fetch_all(
        """
        SELECT user_id, staff_code, email, password, full_name, role, phone, department, status, created_at, last_login_at
        FROM users
        ORDER BY role DESC, full_name ASC
        """
    )
    return [UserAccount(**row) for row in rows]


def normalize_phone(phone: str) -> str:
    normalized_phone = re.sub(r"\D", "", phone or "")
    if len(normalized_phone) < 8:
        raise HTTPException(status_code=400, detail="Số điện thoại không hợp lệ.")
    return normalized_phone


def normalize_email(email: str) -> str:
    normalized_email = email.strip().lower()
    if "@" not in normalized_email:
        raise HTTPException(status_code=400, detail="Email không hợp lệ.")
    return normalized_email


def validate_customer_birth_year(birth_year: int) -> int:
    current_year = datetime.now().year
    age = current_year - birth_year
    if age < 18:
        raise HTTPException(status_code=400, detail="Khách hàng phải từ 18 tuổi trở lên.")
    return birth_year


def build_customer_id(phone: str) -> str:
    return f"customer-{phone}"


def build_demo_user_profile_from_internal(user: dict) -> DemoUserProfile:
    return DemoUserProfile(
        id=user["user_id"],
        role=user["role"],
        name=user["full_name"],
        email=user["email"],
        phone=user["phone"],
        department=user["department"],
        shipping_address=None,
        birth_year=None,
        status=user["status"],
    )


def build_demo_user_profile_from_customer(customer: dict) -> DemoUserProfile:
    return DemoUserProfile(
        id=customer["customer_id"],
        role="customer",
        name=customer["full_name"],
        email=customer["email"],
        phone=customer["phone"],
        department=None,
        shipping_address=customer["shipping_address"],
        birth_year=customer["birth_year"],
        status=customer["status"],
    )


def get_customer_record(customer_id: str) -> dict:
    customer = fetch_one(
        """
        SELECT customer_id, phone, email, password, full_name, shipping_address, birth_year, status, created_at
        FROM customers
        WHERE customer_id = ?
        """,
        (customer_id,),
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng trong hệ thống.")
    return customer


def list_customers_data() -> list[CustomerProfile]:
    rows = fetch_all(
        """
        SELECT customer_id, phone, email, full_name, shipping_address, birth_year, status, created_at
        FROM customers
        ORDER BY created_at DESC, full_name ASC
        """
    )
    return [CustomerProfile(**row) for row in rows]


def create_customer_account(payload: CustomerRegisterRequest) -> CustomerProfile:
    normalized_phone = normalize_phone(payload.phone)
    normalized_email = normalize_email(payload.email)
    validate_customer_birth_year(payload.birth_year)
    customer_id = build_customer_id(normalized_phone)

    if fetch_one("SELECT customer_id FROM customers WHERE phone = ?", (normalized_phone,)):
        raise HTTPException(status_code=409, detail="Số điện thoại này đã tồn tại trong hệ thống.")
    if fetch_one("SELECT customer_id FROM customers WHERE email = ?", (normalized_email,)):
        raise HTTPException(status_code=409, detail="Email này đã tồn tại trong hệ thống khách hàng.")

    with get_connection() as connection:
        created_at = get_current_timestamp(connection)
        connection.execute(
            """
            INSERT INTO customers (
                customer_id,
                phone,
                email,
                password,
                full_name,
                shipping_address,
                birth_year,
                status,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                customer_id,
                normalized_phone,
                normalized_email,
                payload.password,
                payload.full_name.strip(),
                payload.shipping_address.strip(),
                payload.birth_year,
                "active",
                created_at,
            ),
        )
        connection.commit()

    return CustomerProfile(
        customer_id=customer_id,
        phone=normalized_phone,
        email=normalized_email,
        full_name=payload.full_name.strip(),
        shipping_address=payload.shipping_address.strip(),
        birth_year=payload.birth_year,
        status="active",
        created_at=created_at,
    )


def demo_login_user(payload: DemoLoginRequest) -> DemoLoginResponse:
    normalized_identifier = payload.identifier.strip().lower()
    normalized_phone = re.sub(r"\D", "", payload.identifier or "")

    internal_user = fetch_one(
        """
        SELECT user_id, email, password, full_name, role, phone, department, status
        FROM users
        WHERE lower(email) = ?
        """,
        (normalized_identifier,),
    )
    if internal_user and internal_user["password"] == payload.password:
        return DemoLoginResponse(user=build_demo_user_profile_from_internal(internal_user))

    customer = fetch_one(
        """
        SELECT customer_id, phone, email, password, full_name, shipping_address, birth_year, status
        FROM customers
        WHERE phone = ? OR lower(email) = ?
        """,
        (normalized_phone, normalized_identifier),
    )
    if customer and customer["password"] == payload.password:
        return DemoLoginResponse(user=build_demo_user_profile_from_customer(customer))

    raise HTTPException(status_code=401, detail="Thông tin đăng nhập không đúng.")


def require_customer(customer_id: str) -> dict:
    return get_customer_record(customer_id)


def get_cart_rows(customer_id: str) -> list[dict]:
    require_customer(customer_id)
    return fetch_all(
        """
        SELECT
            cci.cart_item_id,
            cci.customer_id,
            cci.account_id,
            la.name AS account_name,
            la.platform_code AS platform,
            pf.display_name AS platform_display_name,
            cci.product_id,
            p.name AS product_name,
            p.sku AS product_sku,
            p.category AS product_category,
            cci.quantity,
            cci.unit_price,
            cci.original_price,
            cci.added_at
        FROM customer_cart_items cci
        JOIN livestream_accounts la ON la.account_id = cci.account_id
        JOIN platforms pf ON pf.code = la.platform_code
        JOIN products p ON p.product_id = cci.product_id
        WHERE cci.customer_id = ?
        ORDER BY cci.added_at DESC
        """,
        (customer_id,),
    )


def list_cart_items_data(customer_id: str) -> list[CartItemResponse]:
    rows = get_cart_rows(customer_id)
    return [
        CartItemResponse(
            **row,
            line_total=round(row["quantity"] * row["unit_price"], 2),
        )
        for row in rows
    ]


def resolve_product_live_price(connection, account_id: str, product_id: str) -> tuple[float, float]:
    assignment = connection.execute(
        """
        SELECT assignment_id
        FROM livestream_product_assignments
        WHERE account_id = ? AND product_id = ?
        """,
        (account_id, product_id),
    ).fetchone()
    if not assignment:
        raise HTTPException(status_code=400, detail="Sản phẩm chưa được gán cho phiên live đã chọn.")

    product = connection.execute(
        """
        SELECT product_id, retail_price, stock_quantity
        FROM products
        WHERE product_id = ?
        """,
        (product_id,),
    ).fetchone()
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm trong hệ thống.")

    live_offer = connection.execute(
        """
        SELECT live_price, original_price
        FROM livestream_product_offers
        WHERE account_id = ? AND product_id = ?
        """,
        (account_id, product_id),
    ).fetchone()
    if live_offer:
        return float(live_offer["live_price"]), float(live_offer["original_price"])
    return float(product["retail_price"]), float(product["retail_price"])


def upsert_cart_item(customer_id: str, payload: CartItemCreateRequest) -> CartMutationResponse:
    require_customer(customer_id)
    with get_connection() as connection:
        account = connection.execute(
            """
            SELECT account_id
            FROM livestream_accounts
            WHERE account_id = ?
            """,
            (payload.account_id,),
        ).fetchone()
        if not account:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiên live đã chọn.")

        unit_price, original_price = resolve_product_live_price(connection, payload.account_id, payload.product_id)
        existing = connection.execute(
            """
            SELECT cart_item_id, quantity
            FROM customer_cart_items
            WHERE customer_id = ? AND account_id = ? AND product_id = ?
            """,
            (customer_id, payload.account_id, payload.product_id),
        ).fetchone()
        added_at = get_current_timestamp(connection)
        if existing:
            connection.execute(
                """
                UPDATE customer_cart_items
                SET quantity = ?, unit_price = ?, original_price = ?, added_at = ?
                WHERE cart_item_id = ?
                """,
                (
                    existing["quantity"] + payload.quantity,
                    unit_price,
                    original_price,
                    added_at,
                    existing["cart_item_id"],
                ),
            )
        else:
            connection.execute(
                """
                INSERT INTO customer_cart_items (
                    cart_item_id,
                    customer_id,
                    account_id,
                    product_id,
                    quantity,
                    unit_price,
                    original_price,
                    added_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"cart-item-{uuid4().hex[:12]}",
                    customer_id,
                    payload.account_id,
                    payload.product_id,
                    payload.quantity,
                    unit_price,
                    original_price,
                    added_at,
                ),
            )
        connection.commit()

    return CartMutationResponse(
        message="Đã cập nhật giỏ hàng của khách hàng.",
        items=list_cart_items_data(customer_id),
    )


def delete_cart_item(customer_id: str, cart_item_id: str) -> CartMutationResponse:
    require_customer(customer_id)
    with get_connection() as connection:
        deleted = connection.execute(
            """
            DELETE FROM customer_cart_items
            WHERE customer_id = ? AND cart_item_id = ?
            """,
            (customer_id, cart_item_id),
        )
        connection.commit()
        if deleted.rowcount == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm trong giỏ hàng.")

    return CartMutationResponse(
        message="Đã xóa sản phẩm khỏi giỏ hàng.",
        items=list_cart_items_data(customer_id),
    )


def clear_cart(customer_id: str) -> CartMutationResponse:
    require_customer(customer_id)
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM customer_cart_items WHERE customer_id = ?",
            (customer_id,),
        )
        connection.commit()

    return CartMutationResponse(
        message="Đã xóa toàn bộ giỏ hàng của khách hàng.",
        items=[],
    )


def build_order_response(connection, order_id: str) -> CustomerOrder:
    order = connection.execute(
        """
        SELECT
            co.order_id,
            co.customer_id,
            co.account_id,
            la.name AS account_name,
            la.platform_code AS platform,
            pf.display_name AS platform_display_name,
            co.total_amount,
            co.shipping_address,
            co.status,
            co.created_at
        FROM customer_orders co
        JOIN livestream_accounts la ON la.account_id = co.account_id
        JOIN platforms pf ON pf.code = la.platform_code
        WHERE co.order_id = ?
        """,
        (order_id,),
    ).fetchone()
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng sau khi checkout.")

    items = connection.execute(
        """
        SELECT
            order_item_id,
            product_id,
            product_name,
            quantity,
            unit_price,
            original_price
        FROM customer_order_items
        WHERE order_id = ?
        ORDER BY order_item_id ASC
        """,
        (order_id,),
    ).fetchall()
    return CustomerOrder(
        **dict(order),
        items=[
            CustomerOrderItem(
                **dict(item),
                line_total=round(item["quantity"] * item["unit_price"], 2),
            )
            for item in items
        ],
    )


def checkout_customer_cart(customer_id: str) -> CheckoutResponse:
    customer = require_customer(customer_id)
    with get_connection() as connection:
        cart_rows = connection.execute(
            """
            SELECT
                cci.cart_item_id,
                cci.customer_id,
                cci.account_id,
                cci.product_id,
                cci.quantity,
                cci.unit_price,
                cci.original_price,
                p.name AS product_name,
                p.stock_quantity,
                p.sku,
                p.category,
                p.brand,
                p.cost_price,
                p.retail_price,
                p.reorder_level,
                p.unit,
                p.description,
                p.is_active
            FROM customer_cart_items cci
            JOIN products p ON p.product_id = cci.product_id
            WHERE cci.customer_id = ?
            ORDER BY cci.account_id ASC, cci.added_at ASC
            """,
            (customer_id,),
        ).fetchall()
        if not cart_rows:
            raise HTTPException(status_code=400, detail="Giỏ hàng đang trống nên chưa thể checkout.")

        for cart_row in cart_rows:
            if cart_row["stock_quantity"] < cart_row["quantity"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Sản phẩm {cart_row['product_name']} không đủ tồn kho để checkout.",
                )

        grouped_rows: dict[str, list[dict]] = {}
        for cart_row in cart_rows:
            grouped_rows.setdefault(cart_row["account_id"], []).append(dict(cart_row))

        created_order_ids: list[str] = []
        for account_id, items in grouped_rows.items():
            created_at = get_current_timestamp(connection)
            order_id = f"order-{uuid4().hex[:12]}"
            total_amount = round(sum(item["quantity"] * item["unit_price"] for item in items), 2)
            connection.execute(
                """
                INSERT INTO customer_orders (
                    order_id,
                    customer_id,
                    account_id,
                    total_amount,
                    shipping_address,
                    status,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    customer_id,
                    account_id,
                    total_amount,
                    customer["shipping_address"],
                    "confirmed",
                    created_at,
                ),
            )
            created_order_ids.append(order_id)

            for item in items:
                connection.execute(
                    """
                    INSERT INTO customer_order_items (
                        order_item_id,
                        order_id,
                        product_id,
                        product_name,
                        quantity,
                        unit_price,
                        original_price
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"order-item-{uuid4().hex[:12]}",
                        order_id,
                        item["product_id"],
                        item["product_name"],
                        item["quantity"],
                        item["unit_price"],
                        item["original_price"],
                    ),
                )
                connection.execute(
                    """
                    UPDATE products
                    SET stock_quantity = stock_quantity - ?
                    WHERE product_id = ?
                    """,
                    (item["quantity"], item["product_id"]),
                )

                updated_product = connection.execute(
                    """
                    SELECT
                        product_id,
                        sku,
                        name,
                        category,
                        brand,
                        cost_price,
                        retail_price,
                        stock_quantity,
                        reorder_level,
                        unit,
                        description,
                        is_active
                    FROM products
                    WHERE product_id = ?
                    """,
                    (item["product_id"],),
                ).fetchone()
                if updated_product:
                    save_json_record("products", dict(updated_product))

        connection.execute(
            "DELETE FROM customer_cart_items WHERE customer_id = ?",
            (customer_id,),
        )
        connection.commit()

        orders = [build_order_response(connection, order_id) for order_id in created_order_ids]

    return CheckoutResponse(
        message="Đã checkout thành công và đồng bộ đơn hàng vào database.",
        orders=orders,
    )


def list_customer_orders(customer_id: str) -> list[CustomerOrder]:
    require_customer(customer_id)
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT order_id
            FROM customer_orders
            WHERE customer_id = ?
            ORDER BY created_at DESC
            """,
            (customer_id,),
        ).fetchall()
        return [build_order_response(connection, row["order_id"]) for row in rows]


def get_livestream_account_record(account_id: str) -> dict:
    account = fetch_one(
        """
        SELECT account_id, name, owner_user_id, owner_name
        FROM livestream_accounts
        WHERE account_id = ?
        """,
        (account_id,),
    )
    if not account:
        raise HTTPException(status_code=404, detail="Không tìm thấy phòng livestream đã chọn.")
    return account


def get_product_basic_record(product_id: str) -> dict:
    product = fetch_one(
        """
        SELECT product_id, name
        FROM products
        WHERE product_id = ?
        """,
        (product_id,),
    )
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm trong hệ thống.")
    return product


def normalize_comment_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def fallback_comment_analysis(comment: str) -> dict:
    normalized = normalize_comment_text(comment)
    buying_keywords = ["chốt", "mua", "lấy", "đặt", "inbox", "ship", "bao nhiêu", "giá"]
    consult_keywords = ["tư vấn", "phù hợp", "thành phần", "da dầu", "da nhạy cảm"]
    if any(keyword in normalized for keyword in buying_keywords):
        intent = "buying_intent"
        priority = "high"
        should_auto_message = True
    elif any(keyword in normalized for keyword in consult_keywords):
        intent = "consult_request"
        priority = "medium"
        should_auto_message = True
    else:
        intent = "other"
        priority = "low"
        should_auto_message = False
    return {
        "intent": intent,
        "sentiment": "positive" if should_auto_message else "neutral",
        "priority": priority,
        "should_auto_message": should_auto_message,
        "auto_message": None,
    }


def analyze_comment_with_ai(comment: str, customer_name: str, account_id: str) -> dict:
    payload = {
        "comment": comment,
        "username": customer_name,
        "account_id": account_id,
    }
    try:
        response = httpx.post(f"{AI_SERVICE_URL}/analyze-comment", json=payload, timeout=5.0)
        response.raise_for_status()
        data = response.json()
        return {
            "intent": data.get("intent", "other"),
            "sentiment": data.get("sentiment", "neutral"),
            "priority": data.get("priority", "low"),
            "should_auto_message": bool(data.get("should_auto_message")),
            "auto_message": data.get("auto_message"),
        }
    except httpx.HTTPError:
        return fallback_comment_analysis(comment)


def get_livestream_comment_detail(comment_id: str) -> LivestreamComment:
    row = fetch_one(
        """
        SELECT
            lc.comment_id,
            lc.account_id,
            la.name AS account_name,
            lc.customer_id,
            c.full_name AS customer_name,
            c.phone AS customer_phone,
            lc.product_id,
            p.name AS product_name,
            lc.content,
            lc.intent,
            lc.sentiment,
            lc.priority,
            lc.should_auto_message,
            lc.created_at
        FROM livestream_comments lc
        JOIN livestream_accounts la ON la.account_id = lc.account_id
        JOIN customers c ON c.customer_id = lc.customer_id
        JOIN products p ON p.product_id = lc.product_id
        WHERE lc.comment_id = ?
        """,
        (comment_id,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Không tìm thấy bình luận trong phiên live.")
    return LivestreamComment(**{**row, "should_auto_message": bool(row["should_auto_message"])})


def list_livestream_comments_data(account_id: str) -> list[LivestreamComment]:
    get_livestream_account_record(account_id)
    rows = fetch_all(
        """
        SELECT
            lc.comment_id,
            lc.account_id,
            la.name AS account_name,
            lc.customer_id,
            c.full_name AS customer_name,
            c.phone AS customer_phone,
            lc.product_id,
            p.name AS product_name,
            lc.content,
            lc.intent,
            lc.sentiment,
            lc.priority,
            lc.should_auto_message,
            lc.created_at
        FROM livestream_comments lc
        JOIN livestream_accounts la ON la.account_id = lc.account_id
        JOIN customers c ON c.customer_id = lc.customer_id
        JOIN products p ON p.product_id = lc.product_id
        WHERE lc.account_id = ?
        ORDER BY lc.created_at DESC
        """,
        (account_id,),
    )
    return [LivestreamComment(**{**row, "should_auto_message": bool(row["should_auto_message"])}) for row in rows]


def get_livestream_message_detail(message_id: str) -> LivestreamMessage:
    row = fetch_one(
        """
        SELECT
            cm.message_id,
            cm.account_id,
            la.name AS account_name,
            cm.customer_id,
            c.full_name AS customer_name,
            c.phone AS customer_phone,
            cm.sender_id,
            cm.sender_role,
            cm.sender_name,
            cm.content,
            cm.source,
            cm.created_at
        FROM conversation_messages cm
        JOIN livestream_accounts la ON la.account_id = cm.account_id
        JOIN customers c ON c.customer_id = cm.customer_id
        WHERE cm.message_id = ?
        """,
        (message_id,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Không tìm thấy tin nhắn trong hội thoại.")
    return LivestreamMessage(**row)


def list_livestream_messages_data(account_id: str, customer_id: str | None = None) -> list[LivestreamMessage]:
    get_livestream_account_record(account_id)
    params: tuple = (account_id,)
    query = """
        SELECT
            cm.message_id,
            cm.account_id,
            la.name AS account_name,
            cm.customer_id,
            c.full_name AS customer_name,
            c.phone AS customer_phone,
            cm.sender_id,
            cm.sender_role,
            cm.sender_name,
            cm.content,
            cm.source,
            cm.created_at
        FROM conversation_messages cm
        JOIN livestream_accounts la ON la.account_id = cm.account_id
        JOIN customers c ON c.customer_id = cm.customer_id
        WHERE cm.account_id = ?
    """
    if customer_id:
        require_customer(customer_id)
        query += " AND cm.customer_id = ?"
        params = (account_id, customer_id)
    query += " ORDER BY cm.created_at ASC"
    rows = fetch_all(query, params)
    return [LivestreamMessage(**row) for row in rows]


def get_ai_assistant_settings_data() -> AiAssistantSettings:
    row = fetch_one(
        """
        SELECT settings_id, is_enabled, customer_reply_template, updated_at
        FROM ai_assistant_settings
        WHERE settings_id = 'default'
        """
    )
    if not row:
        raise HTTPException(status_code=404, detail="Không tìm thấy cấu hình AI.")
    return AiAssistantSettings(
        settings_id=row["settings_id"],
        is_enabled=bool(row["is_enabled"]),
        customer_reply_template=row["customer_reply_template"],
        updated_at=row["updated_at"],
    )


def update_ai_assistant_settings_data(payload: AiAssistantSettingsUpdate) -> AiAssistantSettings:
    template = payload.customer_reply_template.strip()
    if "{customer_name}" not in template:
        raise HTTPException(status_code=400, detail="Mẫu trả lời AI phải chứa biến {customer_name}.")

    with get_connection() as connection:
        updated_at = get_current_timestamp(connection)
        connection.execute(
            """
            UPDATE ai_assistant_settings
            SET is_enabled = ?, customer_reply_template = ?, updated_at = ?
            WHERE settings_id = 'default'
            """,
            (int(payload.is_enabled), template, updated_at),
        )
        connection.commit()

    return get_ai_assistant_settings_data()


def maybe_create_ai_outreach_message(connection, account_id: str, customer: dict, analysis: dict) -> str | None:
    settings_row = connection.execute(
        """
        SELECT is_enabled, customer_reply_template
        FROM ai_assistant_settings
        WHERE settings_id = 'default'
        """
    ).fetchone()
    if settings_row and not bool(settings_row["is_enabled"]):
        return None
    if not analysis.get("should_auto_message"):
        return None

    existing_ai_message = connection.execute(
        """
        SELECT message_id
        FROM conversation_messages
        WHERE account_id = ? AND customer_id = ? AND source = 'ai'
        LIMIT 1
        """,
        (account_id, customer["customer_id"]),
    ).fetchone()
    if existing_ai_message:
        return None

    message_id = f"msg-{uuid4().hex[:12]}"
    default_message = (
        f"Chào {customer['full_name']}, SmartLive thấy bạn đang quan tâm sản phẩm trong live. "
        "Shop đã mở hội thoại để nhân viên hỗ trợ bạn chốt đơn nhanh hơn."
    )
    generated_ai_message = (
        settings_row["customer_reply_template"].replace("{customer_name}", customer["full_name"])
        if settings_row and settings_row["customer_reply_template"]
        else default_message
    )
    connection.execute(
        """
        INSERT INTO conversation_messages (
            message_id,
            account_id,
            customer_id,
            sender_id,
            sender_role,
            sender_name,
            content,
            source,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            message_id,
            account_id,
            customer["customer_id"],
            "ai-assistant",
            "ai",
            "SmartLive AI",
            analysis.get("auto_message") or generated_ai_message,
            "ai",
            get_current_timestamp(connection),
        ),
    )
    return message_id


def create_livestream_comment(payload: LivestreamCommentCreateRequest) -> LivestreamCommentCreateResponse:
    customer = require_customer(payload.customer_id)
    get_livestream_account_record(payload.account_id)
    get_product_basic_record(payload.product_id)
    analysis = analyze_comment_with_ai(payload.content, customer["full_name"], payload.account_id)

    with get_connection() as connection:
        comment_id = f"comment-{uuid4().hex[:12]}"
        created_at = get_current_timestamp(connection)
        connection.execute(
            """
            INSERT INTO livestream_comments (
                comment_id,
                account_id,
                customer_id,
                product_id,
                content,
                intent,
                sentiment,
                priority,
                should_auto_message,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                comment_id,
                payload.account_id,
                payload.customer_id,
                payload.product_id,
                payload.content.strip(),
                analysis["intent"],
                analysis["sentiment"],
                analysis["priority"],
                int(bool(analysis["should_auto_message"])),
                created_at,
            ),
        )
        ai_message_id = maybe_create_ai_outreach_message(connection, payload.account_id, customer, analysis)
        connection.commit()

    ai_message = get_livestream_message_detail(ai_message_id) if ai_message_id else None

    return LivestreamCommentCreateResponse(
        message="Đã ghi nhận bình luận của khách hàng trong phiên live.",
        comment=get_livestream_comment_detail(comment_id),
        auto_message_sent=bool(ai_message),
        auto_message_preview=ai_message.content if ai_message else None,
    )


def create_livestream_message(payload: LivestreamMessageCreateRequest) -> LivestreamMessage:
    get_livestream_account_record(payload.account_id)
    customer = require_customer(payload.customer_id)
    sender_role = payload.sender_role.strip().lower()

    if sender_role == "customer":
        if payload.sender_id != payload.customer_id:
            raise HTTPException(status_code=400, detail="Khách hàng chỉ được trả lời trong chính hội thoại của mình.")
        sender_name = customer["full_name"]
    elif sender_role in STAFF_REPLY_ROLES:
        user = get_user_record(payload.sender_id)
        if user["role"] not in STAFF_REPLY_ROLES:
            raise HTTPException(status_code=400, detail="Chỉ nhân viên bán hàng hoặc admin mới được trả lời khách.")
        sender_name = user["full_name"]
    else:
        raise HTTPException(status_code=400, detail="Vai trò gửi tin nhắn không hợp lệ cho hội thoại live.")

    with get_connection() as connection:
        message_id = f"msg-{uuid4().hex[:12]}"
        connection.execute(
            """
            INSERT INTO conversation_messages (
                message_id,
                account_id,
                customer_id,
                sender_id,
                sender_role,
                sender_name,
                content,
                source,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                payload.account_id,
                payload.customer_id,
                payload.sender_id,
                sender_role,
                sender_name,
                payload.content.strip(),
                payload.source.strip().lower(),
                get_current_timestamp(connection),
            ),
        )
        connection.commit()

    return get_livestream_message_detail(message_id)


@app.get("/")
def root():
    return {
        "service": "account-service",
        "domain": "identity",
        "status": "ok",
        "message": "Identity Service is running.",
        "docs_url": "/docs",
        "health_url": "/health",
        "main_routes": [
            "/users",
            "/users/staff",
            "/users/managed",
            "/demo/login",
            "/customers/register",
            "/customers",
            "/livestream-comments",
            "/livestream-messages",
        ],
    }


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="account-service")


@app.get("/users", response_model=list[UserAccount])
def list_users() -> list[UserAccount]:
    return list_users_data()


@app.post("/demo/login", response_model=DemoLoginResponse)
def demo_login(payload: DemoLoginRequest) -> DemoLoginResponse:
    return demo_login_user(payload)


@app.get("/customers", response_model=list[CustomerProfile])
def list_customers() -> list[CustomerProfile]:
    return list_customers_data()


@app.get("/ai-assistant/settings", response_model=AiAssistantSettings)
def get_ai_assistant_settings() -> AiAssistantSettings:
    return get_ai_assistant_settings_data()


@app.patch("/ai-assistant/settings", response_model=AiAssistantSettings)
def update_ai_assistant_settings(payload: AiAssistantSettingsUpdate) -> AiAssistantSettings:
    return update_ai_assistant_settings_data(payload)


@app.post("/customers/register", response_model=CustomerProfile)
def register_customer(payload: CustomerRegisterRequest) -> CustomerProfile:
    return create_customer_account(payload)


@app.get("/customers/{customer_id}/cart", response_model=list[CartItemResponse])
def list_customer_cart(customer_id: str) -> list[CartItemResponse]:
    return list_cart_items_data(customer_id)


@app.post("/customers/{customer_id}/cart/items", response_model=CartMutationResponse)
def add_customer_cart_item(customer_id: str, payload: CartItemCreateRequest) -> CartMutationResponse:
    return upsert_cart_item(customer_id, payload)


@app.delete("/customers/{customer_id}/cart/items/{cart_item_id}", response_model=CartMutationResponse)
def remove_customer_cart_item(customer_id: str, cart_item_id: str) -> CartMutationResponse:
    return delete_cart_item(customer_id, cart_item_id)


@app.delete("/customers/{customer_id}/cart", response_model=CartMutationResponse)
def clear_customer_cart(customer_id: str) -> CartMutationResponse:
    return clear_cart(customer_id)


@app.post("/customers/{customer_id}/checkout", response_model=CheckoutResponse)
def checkout_customer(customer_id: str) -> CheckoutResponse:
    return checkout_customer_cart(customer_id)


@app.get("/customers/{customer_id}/orders", response_model=list[CustomerOrder])
def list_orders(customer_id: str) -> list[CustomerOrder]:
    return list_customer_orders(customer_id)


@app.get("/livestream-accounts/{account_id}/comments", response_model=list[LivestreamComment])
def list_livestream_comments(account_id: str) -> list[LivestreamComment]:
    return list_livestream_comments_data(account_id)


@app.post("/livestream-comments", response_model=LivestreamCommentCreateResponse)
def create_comment(payload: LivestreamCommentCreateRequest) -> LivestreamCommentCreateResponse:
    return create_livestream_comment(payload)


@app.get("/livestream-accounts/{account_id}/messages", response_model=list[LivestreamMessage])
def list_livestream_messages(account_id: str, customer_id: str | None = None) -> list[LivestreamMessage]:
    return list_livestream_messages_data(account_id, customer_id)


@app.post("/livestream-messages", response_model=LivestreamMessage)
def create_message(payload: LivestreamMessageCreateRequest) -> LivestreamMessage:
    return create_livestream_message(payload)


@app.post("/users/managed", response_model=UserAccount)
def create_managed_user(payload: ManagedUserCreate) -> UserAccount:
    return create_managed_user_account(payload)


@app.post("/users/staff", response_model=UserAccount)
def create_staff_user(payload: StaffUserCreate) -> UserAccount:
    return create_managed_user_account(
        ManagedUserCreate(
            staff_code=payload.staff_code,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            role="staff",
            phone=payload.phone,
            department=payload.department,
            status=payload.status,
        )
    )


@app.patch("/users/{user_id}/password", response_model=UserAccount)
def update_user_password(user_id: str, payload: UserPasswordUpdate) -> UserAccount:
    user = get_user_record(user_id)
    with get_connection() as connection:
        connection.execute(
            "UPDATE users SET password = ? WHERE user_id = ?",
            (payload.password, user_id),
        )
        connection.commit()

    updated_user = {**user, "password": payload.password}
    save_json_record("users", updated_user)
    return UserAccount(**updated_user)


@app.delete("/users/{user_id}", response_model=UserDeleteResponse)
def delete_managed_user(user_id: str) -> UserDeleteResponse:
    user = require_managed_user(user_id)
    owned_accounts = fetch_all(
        """
        SELECT
            account_id,
            account_code,
            name,
            platform_code,
            username,
            password,
            owner_user_id,
            owner_name,
            backup_contact,
            current_viewers,
            max_capacity,
            engagement_rate,
            lag_signal,
            status,
            stream_url,
            warehouse_location,
            shift_label,
            created_at
        FROM livestream_accounts
        WHERE owner_user_id = ?
        """,
        (user_id,),
    )
    product_assignments = fetch_all(
        """
        SELECT assignment_id, account_id, product_id, assigned_by_user_id, assigned_at
        FROM livestream_product_assignments
        WHERE assigned_by_user_id = ?
        """,
        (user_id,),
    )

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE livestream_accounts
            SET owner_user_id = NULL, owner_name = ?
            WHERE owner_user_id = ?
            """,
            ("Chưa gán", user_id),
        )
        connection.execute(
            """
            UPDATE livestream_product_assignments
            SET assigned_by_user_id = NULL
            WHERE assigned_by_user_id = ?
            """,
            (user_id,),
        )
        connection.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        connection.commit()

    delete_json_record("users", user_id)
    for account in owned_accounts:
        save_json_record(
            "livestream_accounts",
            {
                **account,
                "owner_user_id": None,
                "owner_name": "Chưa gán",
            },
        )
    for assignment in product_assignments:
        save_json_record(
            "livestream_product_assignments",
            {**assignment, "assigned_by_user_id": None},
        )

    role_label = "staff" if user["role"] == "staff" else "quản lý sản phẩm"
    return UserDeleteResponse(
        user_id=user_id,
        removed_email=user["email"],
        reassigned_accounts=len(owned_accounts),
        message=f"Đã xóa tài khoản {role_label} khỏi hệ thống.",
    )
