from __future__ import annotations

from collections import defaultdict
import re

from fastapi import FastAPI, HTTPException

from app.database import delete_json_record, get_connection, initialize_database, save_json_record
from app.schemas import (
    DatabaseOverview,
    HealthResponse,
    LivestreamAccount,
    LivestreamAccountCreate,
    LivestreamAccountDeleteResponse,
    PlatformAccountsGroup,
    PlatformSummary,
    ProductItem,
    StaffUserCreate,
    Supplier,
    SupplierOffer,
    UserAccount,
    UserDeleteResponse,
    UserPasswordUpdate,
)

app = FastAPI(
    title="Account Service",
    version="0.3.0",
    description="SQLite-backed account, product, supplier and offer service for livestream management.",
)


@app.on_event("startup")
def startup_event() -> None:
    initialize_database()


def normalize_platform(platform: str) -> str:
    return platform.strip().lower()


def fetch_all(query: str, params: tuple = ()) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def fetch_one(query: str, params: tuple = ()) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(query, params).fetchone()
    return dict(row) if row else None


def list_users_data() -> list[UserAccount]:
    rows = fetch_all(
        """
        SELECT user_id, staff_code, email, password, full_name, role, phone, department, status, created_at, last_login_at
        FROM users
        ORDER BY role DESC, full_name ASC
        """
    )
    return [UserAccount(**row) for row in rows]


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
        raise HTTPException(status_code=404, detail="Khong tim thay tai khoan trong he thong.")
    return user


def require_staff_user(user_id: str) -> dict:
    user = get_user_record(user_id)
    if user["role"] != "staff":
        raise HTTPException(status_code=400, detail="Chi co the thao tac tren tai khoan staff.")
    return user


def normalize_staff_code(staff_code: str) -> str:
    normalized_code = re.sub(r"[^A-Z0-9-]", "", staff_code.strip().upper())
    if len(normalized_code) < 2:
        raise HTTPException(status_code=400, detail="Ma staff phai co it nhat 2 ky tu hop le.")
    return normalized_code


def build_staff_user_id(staff_code: str) -> str:
    return f"user-{staff_code.lower()}"


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
            la.current_viewers,
            la.max_capacity,
            la.engagement_rate,
            la.lag_signal,
            la.status,
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


def list_products_data() -> list[ProductItem]:
    rows = fetch_all(
        """
        SELECT product_id, sku, name, category, brand, cost_price, retail_price, stock_quantity, reorder_level, unit, description, is_active
        FROM products
        ORDER BY category ASC, name ASC
        """
    )
    return [ProductItem(**{**row, "is_active": bool(row["is_active"])}) for row in rows]


def list_suppliers_data() -> list[Supplier]:
    rows = fetch_all(
        """
        SELECT supplier_id, supplier_code, name, contact_name, phone, email, address, rating, lead_time_days, status
        FROM suppliers
        ORDER BY rating DESC, name ASC
        """
    )
    return [Supplier(**row) for row in rows]


def list_supplier_offers_data() -> list[SupplierOffer]:
    rows = fetch_all(
        """
        SELECT
            so.offer_id,
            so.offer_code,
            so.offer_title,
            so.supplier_id,
            s.name AS supplier_name,
            so.product_id,
            p.name AS product_name,
            so.min_order_quantity,
            so.unit_price,
            so.discount_percent,
            so.start_date,
            so.end_date,
            so.status,
            so.notes
        FROM supplier_offers so
        JOIN suppliers s ON s.supplier_id = so.supplier_id
        JOIN products p ON p.product_id = so.product_id
        ORDER BY so.status ASC, so.discount_percent DESC, so.offer_title ASC
        """
    )
    return [SupplierOffer(**row) for row in rows]


def build_platform_summary(platform: str, platform_accounts: list[LivestreamAccount]) -> PlatformSummary:
    total_accounts = len(platform_accounts)
    total_viewers = sum(account.current_viewers for account in platform_accounts)
    total_capacity = sum(account.max_capacity for account in platform_accounts)
    active_accounts = sum(1 for account in platform_accounts if account.status in {"active", "stable", "warning"})
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
        total_viewers=total_viewers,
        total_capacity=total_capacity,
        average_lag_signal=average_lag_signal,
    )


def group_accounts_by_platform() -> list[PlatformAccountsGroup]:
    grouped: dict[str, list[LivestreamAccount]] = defaultdict(list)
    for account in list_livestream_accounts_data():
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
        "service": "account-service",
        "status": "ok",
        "message": "Account Service is running.",
        "docs_url": "/docs",
        "health_url": "/health",
        "main_routes": [
            "/users",
            "/livestream-accounts",
            "/platform-summaries",
            "/products",
            "/database-overview",
        ],
    }


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="account-service")


@app.get("/users", response_model=list[UserAccount])
def list_users() -> list[UserAccount]:
    return list_users_data()


@app.post("/users/staff", response_model=UserAccount)
def create_staff_user(payload: StaffUserCreate) -> UserAccount:
    normalized_staff_code = normalize_staff_code(payload.staff_code)
    user_id = build_staff_user_id(normalized_staff_code)
    normalized_email = payload.email.strip().lower()

    if fetch_one("SELECT user_id FROM users WHERE staff_code = ?", (normalized_staff_code,)):
        raise HTTPException(status_code=409, detail="Ma staff da ton tai. Hay xoa tai khoan cu truoc khi tao lai.")
    if fetch_one("SELECT user_id FROM users WHERE email = ?", (normalized_email,)):
        raise HTTPException(status_code=409, detail="Email nay da ton tai trong he thong.")
    if fetch_one("SELECT user_id FROM users WHERE user_id = ?", (user_id,)):
        raise HTTPException(status_code=409, detail="Ma staff nay dang xung dot voi tai khoan khac trong he thong.")

    with get_connection() as connection:
        created_at = connection.execute("SELECT datetime('now')").fetchone()[0]
        record = {
            "user_id": user_id,
            "staff_code": normalized_staff_code,
            "email": normalized_email,
            "password": payload.password,
            "full_name": payload.full_name.strip(),
            "role": "staff",
            "phone": payload.phone.strip(),
            "department": payload.department.strip(),
            "status": payload.status,
            "created_at": created_at,
            "last_login_at": None,
        }
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


@app.patch("/users/{user_id}/password", response_model=UserAccount)
def update_staff_password(user_id: str, payload: UserPasswordUpdate) -> UserAccount:
    user = require_staff_user(user_id)

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
def delete_staff_user(user_id: str) -> UserDeleteResponse:
    user = require_staff_user(user_id)
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

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE livestream_accounts
            SET owner_user_id = NULL, owner_name = ?
            WHERE owner_user_id = ?
            """,
            ("Chua gan", user_id),
        )
        connection.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        connection.commit()

    delete_json_record("users", user_id)
    for account in owned_accounts:
        updated_account = {
            **account,
            "owner_user_id": None,
            "owner_name": "Chua gan",
        }
        save_json_record("livestream_accounts", updated_account)

    return UserDeleteResponse(
        user_id=user_id,
        removed_email=user["email"],
        reassigned_accounts=len(owned_accounts),
        message="Da xoa tai khoan staff khoi he thong.",
    )


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
        raise HTTPException(status_code=404, detail="Khong tim thay phong livestream trong he thong.")

    with get_connection() as connection:
        connection.execute("DELETE FROM livestream_accounts WHERE account_id = ?", (account_id,))
        connection.commit()

    delete_json_record("livestream_accounts", account_id)
    return LivestreamAccountDeleteResponse(
        account_id=account["account_id"],
        account_name=account["name"],
        message="Da xoa phong livestream khoi he thong.",
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
        raise HTTPException(status_code=404, detail="Khong tim thay tai khoan cho nen tang nay.")
    return filtered_accounts


@app.get("/products", response_model=list[ProductItem])
def list_products() -> list[ProductItem]:
    return list_products_data()


@app.get("/suppliers", response_model=list[Supplier])
def list_suppliers() -> list[Supplier]:
    return list_suppliers_data()


@app.get("/supplier-offers", response_model=list[SupplierOffer])
def list_supplier_offers() -> list[SupplierOffer]:
    return list_supplier_offers_data()


@app.get("/database-overview", response_model=DatabaseOverview)
def get_database_overview() -> DatabaseOverview:
    return DatabaseOverview(
        users=list_users_data(),
        platform_summaries=[group.summary for group in group_accounts_by_platform()],
        livestream_accounts=list_livestream_accounts_data(),
        products=list_products_data(),
        suppliers=list_suppliers_data(),
        supplier_offers=list_supplier_offers_data(),
    )


@app.post("/livestream-accounts", response_model=LivestreamAccount)
def create_livestream_account(payload: LivestreamAccountCreate) -> LivestreamAccount:
    normalized_platform = normalize_platform(payload.platform)
    platform_record = fetch_one(
        "SELECT code, display_name FROM platforms WHERE code = ? AND is_active = 1",
        (normalized_platform,),
    )
    if not platform_record:
        raise HTTPException(status_code=400, detail="Nen tang khong hop le hoac chua duoc cau hinh.")

    owner_user_id = payload.owner_user_id
    if owner_user_id:
        owner_record = fetch_one("SELECT user_id FROM users WHERE user_id = ?", (owner_user_id,))
        if not owner_record:
            raise HTTPException(status_code=400, detail="Khong tim thay owner_user_id trong he thong.")

    with get_connection() as connection:
        sequence = connection.execute(
            "SELECT COUNT(*) AS total FROM livestream_accounts WHERE platform_code = ?",
            (normalized_platform,),
        ).fetchone()[0] + 1
        account_id = f"ls-{normalized_platform}-{sequence:02d}"
        account_code = f"{normalized_platform[:2].upper()}{sequence:02d}"
        created_at = connection.execute("SELECT datetime('now')").fetchone()[0]
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
        save_json_record("livestream_accounts", record)
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
            tuple(record[column] for column in [
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
            ]),
        )
        connection.commit()

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
