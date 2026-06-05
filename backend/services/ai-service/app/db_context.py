from __future__ import annotations

from app.config import settings
from app.schemas import ChatProductContext, ChatVoucherContext, SalesPolicyContext


def _connect():
    if not settings.database_url:
        return None
    try:
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(settings.database_url, row_factory=dict_row, connect_timeout=3)
    except Exception:
        return None


def load_database_context(livestream_id: str | None, shop_id: str | None) -> dict | None:
    """Load grounded sales context from PostgreSQL when available.

    The AI service never depends on this at startup. If DB connection or lookup
    fails, the caller can continue with the already supplied API context.
    """
    conn = _connect()
    if not conn:
        return None
    try:
        with conn:
            with conn.cursor() as cur:
                resolved_shop_id = shop_id
                if livestream_id:
                    cur.execute(
                        """
                        SELECT shop_id::text
                        FROM livestream_db.livestreams
                        WHERE id = %s::uuid
                        """,
                        (livestream_id,),
                    )
                    row = cur.fetchone()
                    if row:
                        resolved_shop_id = row["shop_id"]

                if not resolved_shop_id:
                    return None

                if livestream_id:
                    cur.execute(
                        """
                        SELECT p.id::text AS product_id, p.name, p.category, p.description,
                               p.price::float AS retail_price,
                               COALESCE(p.sale_price, p.price)::float AS live_price,
                               p.stock AS stock_quantity,
                               p.variants, p.image_url, p.purchase_url
                        FROM product_db.products p
                        JOIN livestream_db.livestream_products lp ON lp.product_id = p.id
                        WHERE lp.livestream_id = %s::uuid
                          AND p.shop_id = %s::uuid
                          AND p.status = 'ACTIVE'
                        ORDER BY p.created_at DESC
                        """,
                        (livestream_id, resolved_shop_id),
                    )
                else:
                    cur.execute(
                        """
                        SELECT p.id::text AS product_id, p.name, p.category, p.description,
                               p.price::float AS retail_price,
                               COALESCE(p.sale_price, p.price)::float AS live_price,
                               p.stock AS stock_quantity,
                               p.variants, p.image_url, p.purchase_url
                        FROM product_db.products p
                        WHERE p.shop_id = %s::uuid
                          AND p.status = 'ACTIVE'
                        ORDER BY p.created_at DESC
                        LIMIT 20
                        """,
                        (resolved_shop_id,),
                    )
                product_rows = cur.fetchall()

                cur.execute(
                    """
                    SELECT id::text AS voucher_id, code, discount_type,
                           discount_value::text, min_order_value::float,
                           end_date::text AS valid_until,
                           quantity AS remaining_quantity,
                           status
                    FROM voucher_db.vouchers
                    WHERE shop_id = %s::uuid
                      AND status = 'ACTIVE'
                      AND quantity > 0
                      AND (start_date IS NULL OR start_date <= CURRENT_DATE)
                      AND (end_date IS NULL OR end_date >= CURRENT_DATE)
                    ORDER BY created_at DESC
                    """,
                    (resolved_shop_id,),
                )
                voucher_rows = cur.fetchall()

                cur.execute(
                    """
                    SELECT shipping_fee_note, delivery_time_note, return_policy,
                           sensitive_scope_note
                    FROM shop_db.sales_policies
                    WHERE shop_id = %s::uuid
                    LIMIT 1
                    """,
                    (resolved_shop_id,),
                )
                policy_row = cur.fetchone()

        products = [
            ChatProductContext(
                product_id=row["product_id"],
                name=row["name"],
                category=row.get("category"),
                description=row.get("description") or "",
                retail_price=row.get("retail_price"),
                live_price=row.get("live_price"),
                stock_quantity=row.get("stock_quantity"),
                variants=list(row.get("variants") or []),
                image_url=row.get("image_url"),
                purchase_url=row.get("purchase_url"),
            )
            for row in product_rows
        ]
        vouchers = [
            ChatVoucherContext(
                voucher_id=row["voucher_id"],
                code=row["code"],
                discount_value=f"{row['discount_value']} ({row['discount_type']})",
                conditions=f"Đơn tối thiểu {row['min_order_value']:,.0f} đ".replace(",", "."),
                valid_until=row.get("valid_until"),
                remaining_quantity=row.get("remaining_quantity"),
                applicable_product_ids=[],
            )
            for row in voucher_rows
        ]
        policy = SalesPolicyContext(**policy_row) if policy_row else None
        return {
            "shop_id": resolved_shop_id,
            "products": products,
            "vouchers": vouchers,
            "policy": policy,
            "source": "postgresql",
        }
    except Exception as exc:
        return {"source": "postgresql", "error": str(exc), "products": [], "vouchers": [], "policy": None}
    finally:
        conn.close()
