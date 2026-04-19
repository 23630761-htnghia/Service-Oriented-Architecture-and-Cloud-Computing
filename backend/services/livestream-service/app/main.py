from __future__ import annotations

from collections import defaultdict
import re

from fastapi import FastAPI, HTTPException

from app.database import (
    delete_json_record,
    get_connection,
    initialize_database,
    save_json_record,
)
from app.schemas import (
    HealthResponse,
    LivestreamAccount,
    LivestreamAccountCreate,
    LivestreamAccountDeleteResponse,
    LivestreamPresenceDeleteResponse,
    LivestreamPresenceHeartbeat,
    LivestreamPresenceState,
    LivestreamProductAssignment,
    LivestreamProductAssignmentCreate,
    LivestreamProductAssignmentDeleteResponse,
    LivestreamProductOffer,
    LivestreamProductOfferDeleteResponse,
    LivestreamProductOfferUpsert,
    PlatformAccountsGroup,
    PlatformSummary,
)

app = FastAPI(
    title="Livestream Service",
    version="0.4.0",
    description="Livestream room, platform and product assignment service.",
)


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


def table_exists(table_name: str) -> bool:
    row = fetch_one(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (table_name,),
    )
    return row is not None


def get_current_timestamp(connection) -> str:
    return connection.execute("SELECT datetime('now')").fetchone()[0]


def normalize_platform(platform: str) -> str:
    return platform.strip().lower()


def build_next_sequential_id(connection, table: str, id_column: str, prefix: str) -> str:
    pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)$")
    max_sequence = 0
    rows = connection.execute(f"SELECT {id_column} FROM {table}").fetchall()
    for row in rows:
        match = pattern.match(str(row[id_column]))
        if match:
            max_sequence = max(max_sequence, int(match.group(1)))
    return f"{prefix}-{max_sequence + 1:02d}"


def list_livestream_accounts_data(platform: str | None = None) -> list[LivestreamAccount]:
    query = """
        SELECT
            la.account_id,
            la.account_code,
            la.name,
            la.platform_code AS platform,
            p.display_name AS platform_display_name,
            la.username,
            la.password,
            la.owner_user_id,
            la.owner_name,
            u.email AS owner_email,
            u.password AS owner_password,
            la.backup_contact,
            (
                SELECT COUNT(*)
                FROM livestream_viewer_presence lvp
                WHERE lvp.account_id = la.account_id
                  AND lvp.last_seen_at >= datetime('now', '-15 seconds')
            ) AS current_viewers,
            la.max_capacity,
            la.engagement_rate,
            la.lag_signal,
            la.status,
            CASE
                WHEN EXISTS (
                    SELECT 1
                    FROM livestream_viewer_presence host_presence
                    WHERE host_presence.account_id = la.account_id
                      AND host_presence.is_host = 1
                      AND host_presence.is_live = 1
                      AND host_presence.last_seen_at >= datetime('now', '-15 seconds')
                ) THEN 'live'
                ELSE 'offline'
            END AS broadcast_status,
            CASE
                WHEN EXISTS (
                    SELECT 1
                    FROM livestream_viewer_presence host_presence
                    WHERE host_presence.account_id = la.account_id
                      AND host_presence.is_host = 1
                      AND host_presence.is_live = 1
                      AND host_presence.last_seen_at >= datetime('now', '-15 seconds')
                ) THEN la.live_started_at
                ELSE NULL
            END AS live_started_at,
            (
                SELECT MAX(lvp.last_seen_at)
                FROM livestream_viewer_presence lvp
                WHERE lvp.account_id = la.account_id
                  AND lvp.last_seen_at >= datetime('now', '-15 seconds')
            ) AS last_heartbeat_at,
            la.stream_url,
            la.warehouse_location,
            la.shift_label,
            la.created_at
        FROM livestream_accounts la
        JOIN platforms p ON p.code = la.platform_code
        LEFT JOIN users u ON u.user_id = la.owner_user_id
    """
    params: tuple = ()
    if platform:
        query += " WHERE la.platform_code = ?"
        params = (platform,)
    query += " ORDER BY la.platform_code ASC, la.name ASC"
    rows = fetch_all(query, params)
    return [LivestreamAccount(**row) for row in rows]


def get_account_presence_state(connection, account_id: str) -> LivestreamPresenceState:
    account = connection.execute(
        """
        SELECT account_id, broadcast_status, live_started_at, last_heartbeat_at
        FROM livestream_accounts
        WHERE account_id = ?
        """,
        (account_id,),
    ).fetchone()
    if not account:
        raise HTTPException(status_code=404, detail="Không tìm thấy phòng livestream trong hệ thống.")

    current_viewers = connection.execute(
        """
        SELECT COUNT(*)
        FROM livestream_viewer_presence
        WHERE account_id = ?
          AND last_seen_at >= datetime('now', '-15 seconds')
        """,
        (account_id,),
    ).fetchone()[0]

    has_live_host = connection.execute(
        """
        SELECT 1
        FROM livestream_viewer_presence
        WHERE account_id = ?
          AND is_host = 1
          AND is_live = 1
          AND last_seen_at >= datetime('now', '-15 seconds')
        LIMIT 1
        """,
        (account_id,),
    ).fetchone()
    broadcast_status = "live" if has_live_host else "offline"
    live_started_at = account["live_started_at"] if has_live_host else None
    last_heartbeat_at = account["last_heartbeat_at"] if current_viewers else None

    connection.execute(
        """
        UPDATE livestream_accounts
        SET current_viewers = ?, broadcast_status = ?, live_started_at = ?, last_heartbeat_at = ?
        WHERE account_id = ?
        """,
        (current_viewers, broadcast_status, live_started_at, last_heartbeat_at, account_id),
    )
    return LivestreamPresenceState(
        account_id=account_id,
        current_viewers=current_viewers,
        broadcast_status=broadcast_status,
        live_started_at=live_started_at,
        last_heartbeat_at=last_heartbeat_at,
    )


def heartbeat_livestream_presence(account_id: str, payload: LivestreamPresenceHeartbeat) -> LivestreamPresenceState:
    get_livestream_account_basic_record(account_id)
    with get_connection() as connection:
        timestamp = get_current_timestamp(connection)
        existing = connection.execute(
            """
            SELECT presence_id
            FROM livestream_viewer_presence
            WHERE account_id = ? AND viewer_id = ?
            """,
            (account_id, payload.viewer_id),
        ).fetchone()
        if existing:
            connection.execute(
                """
                UPDATE livestream_viewer_presence
                SET viewer_role = ?, viewer_name = ?, is_host = ?, is_live = ?, last_seen_at = ?
                WHERE account_id = ? AND viewer_id = ?
                """,
                (
                    payload.viewer_role.strip().lower(),
                    payload.viewer_name.strip(),
                    int(payload.is_host),
                    int(payload.is_live),
                    timestamp,
                    account_id,
                    payload.viewer_id,
                ),
            )
        else:
            connection.execute(
                """
                INSERT INTO livestream_viewer_presence (
                    presence_id,
                    account_id,
                    viewer_id,
                    viewer_role,
                    viewer_name,
                    is_host,
                    is_live,
                    last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"presence-{account_id}-{payload.viewer_id}",
                    account_id,
                    payload.viewer_id,
                    payload.viewer_role.strip().lower(),
                    payload.viewer_name.strip(),
                    int(payload.is_host),
                    int(payload.is_live),
                    timestamp,
                ),
            )

        if payload.is_host and payload.is_live:
            current_live_started_at = connection.execute(
                "SELECT live_started_at FROM livestream_accounts WHERE account_id = ?",
                (account_id,),
            ).fetchone()[0]
            if not current_live_started_at:
                connection.execute(
                    """
                    UPDATE livestream_accounts
                    SET live_started_at = ?, last_heartbeat_at = ?
                    WHERE account_id = ?
                    """,
                    (timestamp, timestamp, account_id),
                )
        else:
            connection.execute(
                "UPDATE livestream_accounts SET last_heartbeat_at = ? WHERE account_id = ?",
                (timestamp, account_id),
            )

        state = get_account_presence_state(connection, account_id)
        connection.commit()
        return state


def delete_livestream_presence(account_id: str, viewer_id: str) -> LivestreamPresenceDeleteResponse:
    get_livestream_account_basic_record(account_id)
    with get_connection() as connection:
        deleted = connection.execute(
            """
            DELETE FROM livestream_viewer_presence
            WHERE account_id = ? AND viewer_id = ?
            """,
            (account_id, viewer_id),
        )
        if deleted.rowcount == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy lượt tham gia phiên live cần xóa.")
        get_account_presence_state(connection, account_id)
        connection.commit()

    return LivestreamPresenceDeleteResponse(
        account_id=account_id,
        viewer_id=viewer_id,
        message="Đã xóa lượt tham gia khỏi phiên live.",
    )


def get_product_record(product_id: str) -> dict:
    product = fetch_one(
        """
        SELECT product_id, sku, name, category
        FROM products
        WHERE product_id = ?
        """,
        (product_id,),
    )
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm trong hệ thống.")
    return product


def get_user_record(user_id: str) -> dict:
    user = fetch_one(
        """
        SELECT user_id, full_name, role
        FROM users
        WHERE user_id = ?
        """,
        (user_id,),
    )
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản trong hệ thống.")
    return user


def get_livestream_account_basic_record(account_id: str) -> dict:
    account = fetch_one(
        """
        SELECT la.account_id, la.name, la.platform_code AS platform, p.display_name AS platform_display_name
        FROM livestream_accounts la
        JOIN platforms p ON p.code = la.platform_code
        WHERE la.account_id = ?
        """,
        (account_id,),
    )
    if not account:
        raise HTTPException(status_code=404, detail="Không tìm thấy phòng livestream trong hệ thống.")
    return account


def get_livestream_product_assignment_record(assignment_id: str) -> dict:
    assignment = fetch_one(
        """
        SELECT assignment_id, account_id, product_id
        FROM livestream_product_assignments
        WHERE assignment_id = ?
        """,
        (assignment_id,),
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Không tìm thấy cấu hình sản phẩm cho phòng livestream.")
    return assignment


def ensure_livestream_account_can_be_deleted(account_id: str) -> None:
    dependency_checks = [
        (
            "livestream_product_assignments",
            """
            SELECT 1
            FROM livestream_product_assignments
            WHERE account_id = ?
            LIMIT 1
            """,
            "Không thể xóa phòng livestream đang có sản phẩm được gán.",
        ),
        (
            "livestream_product_offers",
            """
            SELECT 1
            FROM livestream_product_offers
            WHERE account_id = ?
            LIMIT 1
            """,
            "Không thể xóa phòng livestream đang có sản phẩm ghim live.",
        ),
        (
            "customer_cart_items",
            """
            SELECT 1
            FROM customer_cart_items
            WHERE account_id = ?
            LIMIT 1
            """,
            "Không thể xóa phòng livestream đang có sản phẩm trong giỏ hàng của khách.",
        ),
        (
            "customer_orders",
            """
            SELECT 1
            FROM customer_orders
            WHERE account_id = ?
            LIMIT 1
            """,
            "Không thể xóa phòng livestream đã phát sinh đơn hàng.",
        ),
        (
            "livestream_comments",
            """
            SELECT 1
            FROM livestream_comments
            WHERE account_id = ?
            LIMIT 1
            """,
            "Không thể xóa phòng livestream đã phát sinh bình luận.",
        ),
        (
            "conversation_messages",
            """
            SELECT 1
            FROM conversation_messages
            WHERE account_id = ?
            LIMIT 1
            """,
            "Không thể xóa phòng livestream đã phát sinh hội thoại với khách hàng.",
        ),
    ]
    for table_name, query, detail in dependency_checks:
        if not table_exists(table_name):
            continue
        if fetch_one(query, (account_id,)):
            raise HTTPException(status_code=400, detail=detail)


def get_livestream_product_assignment_detail(assignment_id: str) -> LivestreamProductAssignment:
    assignment = fetch_one(
        """
        SELECT
            lpa.assignment_id,
            lpa.account_id,
            la.name AS account_name,
            la.platform_code AS platform,
            pf.display_name AS platform_display_name,
            lpa.product_id,
            p.name AS product_name,
            p.sku AS product_sku,
            p.category AS product_category,
            lpa.assigned_by_user_id,
            u.full_name AS assigned_by_name,
            lpa.assigned_at
        FROM livestream_product_assignments lpa
        JOIN livestream_accounts la ON la.account_id = lpa.account_id
        JOIN platforms pf ON pf.code = la.platform_code
        JOIN products p ON p.product_id = lpa.product_id
        LEFT JOIN users u ON u.user_id = lpa.assigned_by_user_id
        WHERE lpa.assignment_id = ?
        """,
        (assignment_id,),
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Không tìm thấy cấu hình sản phẩm cho phòng livestream.")
    return LivestreamProductAssignment(**assignment)


def list_livestream_product_assignments_data(account_id: str | None = None) -> list[LivestreamProductAssignment]:
    query = """
        SELECT
            lpa.assignment_id,
            lpa.account_id,
            la.name AS account_name,
            la.platform_code AS platform,
            pf.display_name AS platform_display_name,
            lpa.product_id,
            p.name AS product_name,
            p.sku AS product_sku,
            p.category AS product_category,
            lpa.assigned_by_user_id,
            u.full_name AS assigned_by_name,
            lpa.assigned_at
        FROM livestream_product_assignments lpa
        JOIN livestream_accounts la ON la.account_id = lpa.account_id
        JOIN platforms pf ON pf.code = la.platform_code
        JOIN products p ON p.product_id = lpa.product_id
        LEFT JOIN users u ON u.user_id = lpa.assigned_by_user_id
    """
    params: tuple = ()
    if account_id:
        query += " WHERE lpa.account_id = ?"
        params = (account_id,)
    query += " ORDER BY la.name ASC, p.name ASC"
    rows = fetch_all(query, params)
    return [LivestreamProductAssignment(**row) for row in rows]


def get_product_pricing_record(product_id: str) -> dict:
    product = fetch_one(
        """
        SELECT product_id, sku, name, category, retail_price
        FROM products
        WHERE product_id = ?
        """,
        (product_id,),
    )
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm trong hệ thống.")
    return product


def get_livestream_product_offer_detail(account_id: str) -> LivestreamProductOffer:
    offer = fetch_one(
        """
        SELECT
            lpo.live_offer_id,
            lpo.account_id,
            la.name AS account_name,
            la.platform_code AS platform,
            pf.display_name AS platform_display_name,
            lpo.product_id,
            p.name AS product_name,
            p.sku AS product_sku,
            p.category AS product_category,
            lpo.original_price,
            lpo.live_price,
            lpo.pinned_by_user_id,
            u.full_name AS pinned_by_name,
            lpo.pinned_at
        FROM livestream_product_offers lpo
        JOIN livestream_accounts la ON la.account_id = lpo.account_id
        JOIN platforms pf ON pf.code = la.platform_code
        JOIN products p ON p.product_id = lpo.product_id
        LEFT JOIN users u ON u.user_id = lpo.pinned_by_user_id
        WHERE lpo.account_id = ?
        """,
        (account_id,),
    )
    if not offer:
        raise HTTPException(status_code=404, detail="Không tìm thấy live offer cho phiên livestream này.")
    return LivestreamProductOffer(**offer)


def list_livestream_product_offers_data(account_id: str | None = None) -> list[LivestreamProductOffer]:
    query = """
        SELECT
            lpo.live_offer_id,
            lpo.account_id,
            la.name AS account_name,
            la.platform_code AS platform,
            pf.display_name AS platform_display_name,
            lpo.product_id,
            p.name AS product_name,
            p.sku AS product_sku,
            p.category AS product_category,
            lpo.original_price,
            lpo.live_price,
            lpo.pinned_by_user_id,
            u.full_name AS pinned_by_name,
            lpo.pinned_at
        FROM livestream_product_offers lpo
        JOIN livestream_accounts la ON la.account_id = lpo.account_id
        JOIN platforms pf ON pf.code = la.platform_code
        JOIN products p ON p.product_id = lpo.product_id
        LEFT JOIN users u ON u.user_id = lpo.pinned_by_user_id
    """
    params: tuple = ()
    if account_id:
        query += " WHERE lpo.account_id = ?"
        params = (account_id,)
    query += " ORDER BY lpo.pinned_at DESC"
    rows = fetch_all(query, params)
    return [LivestreamProductOffer(**row) for row in rows]


def upsert_livestream_product_offer(payload: LivestreamProductOfferUpsert) -> LivestreamProductOffer:
    get_livestream_account_basic_record(payload.account_id)
    product = get_product_pricing_record(payload.product_id)
    assignment = fetch_one(
        """
        SELECT assignment_id
        FROM livestream_product_assignments
        WHERE account_id = ? AND product_id = ?
        """,
        (payload.account_id, payload.product_id),
    )
    if not assignment:
        raise HTTPException(status_code=400, detail="Sản phẩm chưa được gán cho phiên livestream đã chọn.")
    if payload.live_price > product["retail_price"]:
        raise HTTPException(status_code=400, detail="Giá live không được cao hơn giá gốc.")

    pinned_by_user_id = payload.pinned_by_user_id
    if pinned_by_user_id:
        pinned_by_user = get_user_record(pinned_by_user_id)
        if pinned_by_user["role"] not in {"admin", "staff"}:
            raise HTTPException(
                status_code=400,
                detail="Chỉ admin hoặc staff mới được ghim giá live cho phiên livestream.",
            )

    with get_connection() as connection:
        pinned_at = get_current_timestamp(connection)
        existing_offer = connection.execute(
            """
            SELECT live_offer_id
            FROM livestream_product_offers
            WHERE account_id = ?
            """,
            (payload.account_id,),
        ).fetchone()
        if existing_offer:
            live_offer_id = existing_offer["live_offer_id"]
            connection.execute(
                """
                UPDATE livestream_product_offers
                SET product_id = ?, original_price = ?, live_price = ?, pinned_by_user_id = ?, pinned_at = ?
                WHERE account_id = ?
                """,
                (
                    payload.product_id,
                    product["retail_price"],
                    payload.live_price,
                    pinned_by_user_id,
                    pinned_at,
                    payload.account_id,
                ),
            )
        else:
            live_offer_id = f"live-offer-{payload.account_id}"
            connection.execute(
                """
                INSERT INTO livestream_product_offers (
                    live_offer_id,
                    account_id,
                    product_id,
                    original_price,
                    live_price,
                    pinned_by_user_id,
                    pinned_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    live_offer_id,
                    payload.account_id,
                    payload.product_id,
                    product["retail_price"],
                    payload.live_price,
                    pinned_by_user_id,
                    pinned_at,
                ),
            )
        connection.commit()

    return get_livestream_product_offer_detail(payload.account_id)


def build_platform_summary(platform: str, platform_accounts: list[LivestreamAccount]) -> PlatformSummary:
    total_accounts = len(platform_accounts)
    total_viewers = sum(account.current_viewers for account in platform_accounts)
    total_capacity = sum(account.max_capacity for account in platform_accounts)
    active_accounts = sum(1 for account in platform_accounts if account.status in {"active", "stable", "warning"})
    live_accounts = sum(1 for account in platform_accounts if account.broadcast_status == "live")
    average_lag_signal = 0.0
    if total_accounts:
        average_lag_signal = round(
            sum(account.lag_signal for account in platform_accounts) / total_accounts,
            2,
        )

    return PlatformSummary(
        platform=platform,
        display_name=platform_accounts[0].platform_display_name,
        total_accounts=total_accounts,
        active_accounts=active_accounts,
        live_accounts=live_accounts,
        total_viewers=total_viewers,
        total_capacity=total_capacity,
        average_lag_signal=average_lag_signal,
    )


def group_accounts_by_platform(accounts: list[LivestreamAccount] | None = None) -> list[PlatformAccountsGroup]:
    grouped: dict[str, list[LivestreamAccount]] = defaultdict(list)
    source_accounts = accounts if accounts is not None else list_livestream_accounts_data()
    for account in source_accounts:
        grouped[account.platform].append(account)

    groups: list[PlatformAccountsGroup] = []
    for platform in sorted(grouped):
        platform_accounts = grouped[platform]
        groups.append(
            PlatformAccountsGroup(
                platform=platform,
                display_name=platform_accounts[0].platform_display_name,
                accounts=platform_accounts,
                summary=build_platform_summary(platform, platform_accounts),
            )
        )
    return groups


@app.get("/")
def root():
    return {
        "service": "livestream-service",
        "status": "ok",
        "message": "Livestream Service is running.",
        "docs_url": "/docs",
        "health_url": "/health",
        "main_routes": [
            "/livestream-accounts",
            "/platform-summaries",
            "/livestream-product-assignments",
            "/livestream-product-offers",
        ],
    }


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="livestream-service")


@app.delete("/livestream-accounts/{account_id}", response_model=LivestreamAccountDeleteResponse)
def delete_livestream_account(account_id: str) -> LivestreamAccountDeleteResponse:
    account = fetch_one(
        """
        SELECT account_id, name
        FROM livestream_accounts
        WHERE account_id = ?
        """,
        (account_id,),
    )
    if not account:
        raise HTTPException(status_code=404, detail="Không tìm thấy phòng livestream trong hệ thống.")
    ensure_livestream_account_can_be_deleted(account_id)

    with get_connection() as connection:
        connection.execute("DELETE FROM livestream_accounts WHERE account_id = ?", (account_id,))
        connection.commit()

    delete_json_record("livestream_accounts", account_id)
    return LivestreamAccountDeleteResponse(
        account_id=account["account_id"],
        account_name=account["name"],
        message="Đã xóa phòng livestream khỏi hệ thống.",
    )


@app.get("/livestream-accounts", response_model=list[LivestreamAccount])
def list_livestream_accounts() -> list[LivestreamAccount]:
    return list_livestream_accounts_data()


@app.get("/livestream-accounts/grouped", response_model=list[PlatformAccountsGroup])
def list_grouped_livestream_accounts() -> list[PlatformAccountsGroup]:
    return group_accounts_by_platform()


@app.get("/platform-summaries", response_model=list[PlatformSummary])
def list_platform_summaries() -> list[PlatformSummary]:
    return [group.summary for group in group_accounts_by_platform()]


@app.get("/platforms/{platform}/accounts", response_model=list[LivestreamAccount])
def list_accounts_by_platform(platform: str) -> list[LivestreamAccount]:
    normalized_platform = normalize_platform(platform)
    filtered_accounts = list_livestream_accounts_data(normalized_platform)
    if not filtered_accounts:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản cho nền tảng này.")
    return filtered_accounts


@app.post("/livestream-accounts/{account_id}/presence/heartbeat", response_model=LivestreamPresenceState)
def upsert_livestream_presence(account_id: str, payload: LivestreamPresenceHeartbeat) -> LivestreamPresenceState:
    return heartbeat_livestream_presence(account_id, payload)


@app.delete("/livestream-accounts/{account_id}/presence/{viewer_id}", response_model=LivestreamPresenceDeleteResponse)
def remove_livestream_presence(account_id: str, viewer_id: str) -> LivestreamPresenceDeleteResponse:
    return delete_livestream_presence(account_id, viewer_id)


@app.get("/livestream-product-assignments", response_model=list[LivestreamProductAssignment])
def list_livestream_product_assignments(account_id: str | None = None) -> list[LivestreamProductAssignment]:
    if account_id:
        get_livestream_account_basic_record(account_id)
    return list_livestream_product_assignments_data(account_id)


@app.get("/livestream-product-offers", response_model=list[LivestreamProductOffer])
def list_livestream_product_offers(account_id: str | None = None) -> list[LivestreamProductOffer]:
    if account_id:
        get_livestream_account_basic_record(account_id)
    return list_livestream_product_offers_data(account_id)


@app.post("/livestream-product-offers", response_model=LivestreamProductOffer)
def create_or_update_livestream_product_offer(payload: LivestreamProductOfferUpsert) -> LivestreamProductOffer:
    return upsert_livestream_product_offer(payload)


@app.delete("/livestream-product-offers/{account_id}", response_model=LivestreamProductOfferDeleteResponse)
def delete_livestream_product_offer(account_id: str) -> LivestreamProductOfferDeleteResponse:
    get_livestream_account_basic_record(account_id)
    with get_connection() as connection:
        deleted = connection.execute(
            """
            DELETE FROM livestream_product_offers
            WHERE account_id = ?
            """,
            (account_id,),
        )
        connection.commit()
        if deleted.rowcount == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy live offer để xóa.")
    return LivestreamProductOfferDeleteResponse(
        account_id=account_id,
        message="Đã gỡ live offer khỏi phiên livestream.",
    )


@app.post("/livestream-product-assignments", response_model=LivestreamProductAssignment)
def create_livestream_product_assignment(payload: LivestreamProductAssignmentCreate) -> LivestreamProductAssignment:
    get_livestream_account_basic_record(payload.account_id)
    get_product_record(payload.product_id)

    assigned_by_user_id = payload.assigned_by_user_id
    if assigned_by_user_id:
        assigned_by_user = get_user_record(assigned_by_user_id)
        if assigned_by_user["role"] not in {"admin", "product_manager"}:
            raise HTTPException(
                status_code=400,
                detail="Chỉ admin hoặc quản lý sản phẩm mới được ghi nhận cấu hình gán sản phẩm.",
            )

    duplicate_assignment = fetch_one(
        """
        SELECT assignment_id
        FROM livestream_product_assignments
        WHERE account_id = ? AND product_id = ?
        """,
        (payload.account_id, payload.product_id),
    )
    if duplicate_assignment:
        raise HTTPException(status_code=409, detail="Sản phẩm này đã được gán cho phòng livestream đã chọn.")

    with get_connection() as connection:
        assignment_id = build_next_sequential_id(
            connection,
            "livestream_product_assignments",
            "assignment_id",
            "lap",
        )
        assigned_at = get_current_timestamp(connection)
        record = {
            "assignment_id": assignment_id,
            "account_id": payload.account_id,
            "product_id": payload.product_id,
            "assigned_by_user_id": assigned_by_user_id,
            "assigned_at": assigned_at,
        }
        connection.execute(
            """
            INSERT INTO livestream_product_assignments (
                assignment_id,
                account_id,
                product_id,
                assigned_by_user_id,
                assigned_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                record["assignment_id"],
                record["account_id"],
                record["product_id"],
                record["assigned_by_user_id"],
                record["assigned_at"],
            ),
        )
        connection.commit()

    save_json_record("livestream_product_assignments", record)
    return get_livestream_product_assignment_detail(assignment_id)


@app.delete("/livestream-product-assignments/{assignment_id}", response_model=LivestreamProductAssignmentDeleteResponse)
def delete_livestream_product_assignment(assignment_id: str) -> LivestreamProductAssignmentDeleteResponse:
    assignment = get_livestream_product_assignment_record(assignment_id)

    with get_connection() as connection:
        connection.execute(
            """
            DELETE FROM livestream_product_offers
            WHERE account_id = ? AND product_id = ?
            """,
            (assignment["account_id"], assignment["product_id"]),
        )
        connection.execute(
            "DELETE FROM livestream_product_assignments WHERE assignment_id = ?",
            (assignment_id,),
        )
        connection.commit()

    delete_json_record("livestream_product_assignments", assignment_id)
    return LivestreamProductAssignmentDeleteResponse(
        assignment_id=assignment_id,
        account_id=assignment["account_id"],
        product_id=assignment["product_id"],
        message="Đã gỡ sản phẩm khỏi phòng livestream.",
    )


@app.post("/livestream-accounts", response_model=LivestreamAccount)
def create_livestream_account(payload: LivestreamAccountCreate) -> LivestreamAccount:
    normalized_platform = normalize_platform(payload.platform)
    platform_record = fetch_one(
        "SELECT code, display_name FROM platforms WHERE code = ? AND is_active = 1",
        (normalized_platform,),
    )
    if not platform_record:
        raise HTTPException(status_code=400, detail="Nền tảng không hợp lệ hoặc chưa được cấu hình.")

    owner_user_id = payload.owner_user_id
    if owner_user_id:
        owner_record = fetch_one(
            "SELECT user_id, role FROM users WHERE user_id = ?",
            (owner_user_id,),
        )
        if not owner_record:
            raise HTTPException(status_code=400, detail="Không tìm thấy owner_user_id trong hệ thống.")
        if owner_record["role"] not in {"admin", "staff"}:
            raise HTTPException(
                status_code=400,
                detail="Phòng livestream chỉ có thể gán cho admin hoặc staff phụ trách bán hàng.",
            )

    with get_connection() as connection:
        sequence = connection.execute(
            "SELECT COUNT(*) AS total FROM livestream_accounts WHERE platform_code = ?",
            (normalized_platform,),
        ).fetchone()[0] + 1
        account_id = f"ls-{normalized_platform}-{sequence:02d}"
        account_code = f"{normalized_platform[:2].upper()}{sequence:02d}"
        created_at = get_current_timestamp(connection)
        record = {
            "account_id": account_id,
            "account_code": account_code,
            "name": payload.name,
            "platform_code": normalized_platform,
            "username": payload.username,
            "password": payload.password,
            "owner_user_id": owner_user_id,
            "owner_name": payload.owner_name,
            "backup_contact": payload.backup_contact,
            "current_viewers": payload.current_viewers,
            "max_capacity": payload.max_capacity,
            "engagement_rate": payload.engagement_rate,
            "lag_signal": payload.lag_signal,
            "status": payload.status,
            "stream_url": payload.stream_url,
            "warehouse_location": payload.warehouse_location,
            "shift_label": payload.shift_label,
            "created_at": created_at,
        }
        connection.execute(
            """
            INSERT INTO livestream_accounts (
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
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(
                record[column]
                for column in [
                    "account_id",
                    "account_code",
                    "name",
                    "platform_code",
                    "username",
                    "password",
                    "owner_user_id",
                    "owner_name",
                    "backup_contact",
                    "current_viewers",
                    "max_capacity",
                    "engagement_rate",
                    "lag_signal",
                    "status",
                    "stream_url",
                    "warehouse_location",
                    "shift_label",
                    "created_at",
                ]
            ),
        )
        connection.commit()

    save_json_record("livestream_accounts", record)
    created = fetch_one(
        """
        SELECT
            la.account_id,
            la.account_code,
            la.name,
            la.platform_code AS platform,
            p.display_name AS platform_display_name,
            la.username,
            la.password,
            la.owner_user_id,
            la.owner_name,
            u.email AS owner_email,
            u.password AS owner_password,
            la.backup_contact,
            la.current_viewers,
            la.max_capacity,
            la.engagement_rate,
            la.lag_signal,
            la.status,
            la.broadcast_status,
            la.live_started_at,
            la.last_heartbeat_at,
            la.stream_url,
            la.warehouse_location,
            la.shift_label,
            la.created_at
        FROM livestream_accounts la
        JOIN platforms p ON p.code = la.platform_code
        LEFT JOIN users u ON u.user_id = la.owner_user_id
        WHERE la.account_id = ?
        """,
        (account_id,),
    )
    return LivestreamAccount(**created)
