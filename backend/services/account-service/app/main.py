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
    LivestreamProductAssignment,
    LivestreamProductAssignmentCreate,
    LivestreamProductAssignmentDeleteResponse,
    ManagedUserCreate,
    PlatformAccountsGroup,
    PlatformSummary,
    ProductCreate,
    ProductDeleteResponse,
    ProductItem,
    ProductUpdate,
    StaffUserCreate,
    Supplier,
    SupplierCreate,
    SupplierDeleteResponse,
    SupplierOffer,
    SupplierUpdate,
    UserAccount,
    UserDeleteResponse,
    UserPasswordUpdate,
)

app = FastAPI(
    title="Account Service",
    version="0.3.0",
    description="SQLite-backed account, product, supplier and offer service for livestream management.",
)

MANAGED_USER_ROLES = {"staff", "product_manager"}


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


def get_current_timestamp(connection) -> str:
    return connection.execute("SELECT datetime('now')").fetchone()[0]


def build_product_record(product_id: str, payload: ProductCreate | ProductUpdate) -> dict:
    return {
        "product_id": product_id,
        "sku": normalize_reference_code(payload.sku, "SKU"),
        "name": payload.name.strip(),
        "category": payload.category.strip(),
        "brand": payload.brand.strip(),
        "cost_price": payload.cost_price,
        "retail_price": payload.retail_price,
        "stock_quantity": payload.stock_quantity,
        "reorder_level": payload.reorder_level,
        "unit": payload.unit.strip(),
        "description": payload.description.strip(),
        "is_active": payload.is_active,
    }


def build_supplier_record(supplier_id: str, payload: SupplierCreate | SupplierUpdate) -> dict:
    return {
        "supplier_id": supplier_id,
        "supplier_code": normalize_reference_code(payload.supplier_code, "Mã nhà cung cấp"),
        "name": payload.name.strip(),
        "contact_name": payload.contact_name.strip(),
        "phone": payload.phone.strip(),
        "email": payload.email.strip().lower(),
        "address": payload.address.strip(),
        "rating": payload.rating,
        "lead_time_days": payload.lead_time_days,
        "status": payload.status.strip(),
    }


def validate_managed_role(role: str) -> str:
    normalized_role = role.strip().lower()
    if normalized_role not in MANAGED_USER_ROLES:
        raise HTTPException(status_code=400, detail="Vai trò quản lý không hợp lệ.")
    return normalized_role


def build_managed_user_id(staff_code: str) -> str:
    return f"user-{staff_code.lower()}"


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


def normalize_staff_code(staff_code: str) -> str:
    normalized_code = re.sub(r"[^A-Z0-9-]", "", staff_code.strip().upper())
    if len(normalized_code) < 2:
        raise HTTPException(status_code=400, detail="Mã staff phải có ít nhất 2 ký tự hợp lệ.")
    return normalized_code


def normalize_reference_code(code: str, label: str) -> str:
    normalized_code = re.sub(r"[^A-Z0-9-]", "", code.strip().upper())
    if len(normalized_code) < 2:
        raise HTTPException(status_code=400, detail=f"{label} phải có ít nhất 2 ký tự hợp lệ.")
    return normalized_code


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


def get_product_record(product_id: str) -> dict:
    product = fetch_one(
        """
        SELECT product_id, sku, name, category, brand, cost_price, retail_price, stock_quantity, reorder_level, unit, description, is_active
        FROM products
        WHERE product_id = ?
        """,
        (product_id,),
    )
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm trong hệ thống.")
    return {
        **product,
        "is_active": bool(product["is_active"]),
    }


def list_suppliers_data() -> list[Supplier]:
    rows = fetch_all(
        """
        SELECT supplier_id, supplier_code, name, contact_name, phone, email, address, rating, lead_time_days, status
        FROM suppliers
        ORDER BY rating DESC, name ASC
        """
    )
    return [Supplier(**row) for row in rows]


def get_supplier_record(supplier_id: str) -> dict:
    supplier = fetch_one(
        """
        SELECT supplier_id, supplier_code, name, contact_name, phone, email, address, rating, lead_time_days, status
        FROM suppliers
        WHERE supplier_id = ?
        """,
        (supplier_id,),
    )
    if not supplier:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhà cung cấp trong hệ thống.")
    return supplier


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


def build_database_overview() -> DatabaseOverview:
    livestream_accounts = list_livestream_accounts_data()
    platform_groups = group_accounts_by_platform(livestream_accounts)
    return DatabaseOverview(
        users=list_users_data(),
        platform_summaries=[group.summary for group in platform_groups],
        livestream_accounts=livestream_accounts,
        products=list_products_data(),
        suppliers=list_suppliers_data(),
        supplier_offers=list_supplier_offers_data(),
        livestream_product_assignments=list_livestream_product_assignments_data(),
    )


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
        updated_account = {
            **account,
            "owner_user_id": None,
            "owner_name": "Chưa gán",
        }
        save_json_record("livestream_accounts", updated_account)
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
    linked_assignments = fetch_all(
        """
        SELECT assignment_id
        FROM livestream_product_assignments
        WHERE account_id = ?
        """,
        (account_id,),
    )

    with get_connection() as connection:
        connection.execute("DELETE FROM livestream_accounts WHERE account_id = ?", (account_id,))
        connection.commit()

    delete_json_record("livestream_accounts", account_id)
    for assignment in linked_assignments:
        delete_json_record("livestream_product_assignments", assignment["assignment_id"])
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


@app.get("/products", response_model=list[ProductItem])
def list_products() -> list[ProductItem]:
    return list_products_data()


@app.get("/livestream-product-assignments", response_model=list[LivestreamProductAssignment])
def list_livestream_product_assignments(account_id: str | None = None) -> list[LivestreamProductAssignment]:
    if account_id:
        get_livestream_account_basic_record(account_id)
    return list_livestream_product_assignments_data(account_id)


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


@app.post("/products", response_model=ProductItem)
def create_product(payload: ProductCreate) -> ProductItem:
    normalized_sku = normalize_reference_code(payload.sku, "SKU")
    if fetch_one("SELECT product_id FROM products WHERE sku = ?", (normalized_sku,)):
        raise HTTPException(status_code=409, detail="SKU này đã tồn tại trong hệ thống.")

    with get_connection() as connection:
        product_id = build_next_sequential_id(connection, "products", "product_id", "product")
        record = build_product_record(product_id, payload)
        connection.execute(
            """
            INSERT INTO products (
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
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["product_id"],
                record["sku"],
                record["name"],
                record["category"],
                record["brand"],
                record["cost_price"],
                record["retail_price"],
                record["stock_quantity"],
                record["reorder_level"],
                record["unit"],
                record["description"],
                int(record["is_active"]),
            ),
        )
        connection.commit()

    save_json_record("products", record)
    return ProductItem(**record)


@app.patch("/products/{product_id}", response_model=ProductItem)
def update_product(product_id: str, payload: ProductUpdate) -> ProductItem:
    get_product_record(product_id)
    normalized_sku = normalize_reference_code(payload.sku, "SKU")

    duplicate_product = fetch_one(
        "SELECT product_id FROM products WHERE sku = ? AND product_id <> ?",
        (normalized_sku, product_id),
    )
    if duplicate_product:
        raise HTTPException(status_code=409, detail="SKU này đã được gán cho sản phẩm khác.")

    record = build_product_record(product_id, payload)

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE products
            SET sku = ?, name = ?, category = ?, brand = ?, cost_price = ?, retail_price = ?,
                stock_quantity = ?, reorder_level = ?, unit = ?, description = ?, is_active = ?
            WHERE product_id = ?
            """,
            (
                record["sku"],
                record["name"],
                record["category"],
                record["brand"],
                record["cost_price"],
                record["retail_price"],
                record["stock_quantity"],
                record["reorder_level"],
                record["unit"],
                record["description"],
                int(record["is_active"]),
                product_id,
            ),
        )
        connection.commit()

    save_json_record("products", record)
    return ProductItem(**record)


@app.delete("/products/{product_id}", response_model=ProductDeleteResponse)
def delete_product(product_id: str) -> ProductDeleteResponse:
    product = get_product_record(product_id)
    linked_offer = fetch_one(
        """
        SELECT offer_id
        FROM supplier_offers
        WHERE product_id = ?
        LIMIT 1
        """,
        (product_id,),
    )
    if linked_offer:
        raise HTTPException(
            status_code=400,
            detail="Không thể xóa sản phẩm đang được tham chiếu trong bảng giá nhà cung cấp.",
        )
    linked_assignments = fetch_all(
        """
        SELECT assignment_id
        FROM livestream_product_assignments
        WHERE product_id = ?
        """,
        (product_id,),
    )

    with get_connection() as connection:
        connection.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
        connection.commit()

    delete_json_record("products", product_id)
    for assignment in linked_assignments:
        delete_json_record("livestream_product_assignments", assignment["assignment_id"])
    return ProductDeleteResponse(
        product_id=product_id,
        product_name=product["name"],
        message="Đã xóa sản phẩm khỏi hệ thống.",
    )


@app.get("/suppliers", response_model=list[Supplier])
def list_suppliers() -> list[Supplier]:
    return list_suppliers_data()


@app.post("/suppliers", response_model=Supplier)
def create_supplier(payload: SupplierCreate) -> Supplier:
    normalized_supplier_code = normalize_reference_code(payload.supplier_code, "Mã nhà cung cấp")
    if fetch_one("SELECT supplier_id FROM suppliers WHERE supplier_code = ?", (normalized_supplier_code,)):
        raise HTTPException(status_code=409, detail="Mã nhà cung cấp này đã tồn tại trong hệ thống.")

    with get_connection() as connection:
        supplier_id = build_next_sequential_id(connection, "suppliers", "supplier_id", "supplier")
        record = build_supplier_record(supplier_id, payload)
        connection.execute(
            """
            INSERT INTO suppliers (
                supplier_id,
                supplier_code,
                name,
                contact_name,
                phone,
                email,
                address,
                rating,
                lead_time_days,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["supplier_id"],
                record["supplier_code"],
                record["name"],
                record["contact_name"],
                record["phone"],
                record["email"],
                record["address"],
                record["rating"],
                record["lead_time_days"],
                record["status"],
            ),
        )
        connection.commit()

    save_json_record("suppliers", record)
    return Supplier(**record)


@app.patch("/suppliers/{supplier_id}", response_model=Supplier)
def update_supplier(supplier_id: str, payload: SupplierUpdate) -> Supplier:
    get_supplier_record(supplier_id)
    normalized_supplier_code = normalize_reference_code(payload.supplier_code, "Mã nhà cung cấp")

    duplicate_supplier = fetch_one(
        "SELECT supplier_id FROM suppliers WHERE supplier_code = ? AND supplier_id <> ?",
        (normalized_supplier_code, supplier_id),
    )
    if duplicate_supplier:
        raise HTTPException(status_code=409, detail="Mã nhà cung cấp này đã được gán cho bản ghi khác.")

    record = build_supplier_record(supplier_id, payload)

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE suppliers
            SET supplier_code = ?, name = ?, contact_name = ?, phone = ?, email = ?, address = ?,
                rating = ?, lead_time_days = ?, status = ?
            WHERE supplier_id = ?
            """,
            (
                record["supplier_code"],
                record["name"],
                record["contact_name"],
                record["phone"],
                record["email"],
                record["address"],
                record["rating"],
                record["lead_time_days"],
                record["status"],
                supplier_id,
            ),
        )
        connection.commit()

    save_json_record("suppliers", record)
    return Supplier(**record)


@app.delete("/suppliers/{supplier_id}", response_model=SupplierDeleteResponse)
def delete_supplier(supplier_id: str) -> SupplierDeleteResponse:
    supplier = get_supplier_record(supplier_id)
    linked_offers = fetch_all(
        """
        SELECT offer_id, product_id
        FROM supplier_offers
        WHERE supplier_id = ?
        """,
        (supplier_id,),
    )
    product_ids = sorted({offer["product_id"] for offer in linked_offers})
    removable_product_ids: list[str] = []

    for product_id in product_ids:
        remaining_supplier = fetch_one(
            """
            SELECT supplier_id
            FROM supplier_offers
            WHERE product_id = ? AND supplier_id <> ?
            LIMIT 1
            """,
            (product_id, supplier_id),
        )
        if not remaining_supplier:
            removable_product_ids.append(product_id)

    removable_assignments = fetch_all(
        f"""
        SELECT assignment_id
        FROM livestream_product_assignments
        WHERE product_id IN ({", ".join("?" for _ in removable_product_ids)})
        """
        if removable_product_ids
        else "SELECT assignment_id FROM livestream_product_assignments WHERE 1 = 0",
        tuple(removable_product_ids),
    )

    with get_connection() as connection:
        if removable_product_ids:
            connection.execute(
                f"DELETE FROM products WHERE product_id IN ({', '.join('?' for _ in removable_product_ids)})",
                tuple(removable_product_ids),
            )
        connection.execute(
            "DELETE FROM supplier_offers WHERE supplier_id = ?",
            (supplier_id,),
        )
        connection.execute("DELETE FROM suppliers WHERE supplier_id = ?", (supplier_id,))
        connection.commit()

    delete_json_record("suppliers", supplier_id)
    for offer in linked_offers:
        delete_json_record("supplier_offers", offer["offer_id"])
    for product_id in removable_product_ids:
        delete_json_record("products", product_id)
    for assignment in removable_assignments:
        delete_json_record("livestream_product_assignments", assignment["assignment_id"])

    removed_products_total = len(removable_product_ids)
    return SupplierDeleteResponse(
        supplier_id=supplier_id,
        supplier_name=supplier["name"],
        message=(
            "Đã xóa nhà cung cấp khỏi hệ thống."
            if not removed_products_total
            else f"Đã xóa nhà cung cấp và {removed_products_total} sản phẩm liên quan khỏi hệ thống."
        ),
    )


@app.get("/supplier-offers", response_model=list[SupplierOffer])
def list_supplier_offers() -> list[SupplierOffer]:
    return list_supplier_offers_data()


@app.get("/database-overview", response_model=DatabaseOverview)
def get_database_overview() -> DatabaseOverview:
    return build_database_overview()


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
