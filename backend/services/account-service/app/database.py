from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"
if not DEFAULT_DATA_DIR.exists():
    DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "account-service" / "app" / "data"
DATA_DIR = Path(os.getenv("APP_DATA_DIR", str(DEFAULT_DATA_DIR))).resolve()
LEGACY_DB_PATH = DATA_DIR / "account_management.db"
DB_PATH = DATA_DIR / "sqlite" / "account_management.db"

TABLE_PRIMARY_KEYS = {
    "users": "user_id",
    "platforms": "platform_id",
    "products": "product_id",
    "suppliers": "supplier_id",
    "livestream_accounts": "account_id",
    "supplier_offers": "offer_id",
    "livestream_product_assignments": "assignment_id",
}

TABLE_JSON_DIRS = {
    "users": DATA_DIR / "identity" / "users",
    "platforms": DATA_DIR / "livestream" / "platforms",
    "products": DATA_DIR / "catalog" / "products",
    "suppliers": DATA_DIR / "catalog" / "suppliers",
    "livestream_accounts": DATA_DIR / "livestream" / "accounts",
    "supplier_offers": DATA_DIR / "catalog" / "supplier_offers",
    "livestream_product_assignments": DATA_DIR / "livestream" / "product_assignments",
}

TABLE_INSERT_COLUMNS = {
    "users": ["user_id", "staff_code", "email", "password", "full_name", "role", "phone", "department", "status", "created_at", "last_login_at"],
    "platforms": ["platform_id", "code", "display_name", "category", "region", "is_active"],
    "products": ["product_id", "sku", "name", "category", "brand", "cost_price", "retail_price", "stock_quantity", "reorder_level", "unit", "description", "is_active"],
    "suppliers": ["supplier_id", "supplier_code", "name", "contact_name", "phone", "email", "address", "rating", "lead_time_days", "status"],
    "livestream_accounts": ["account_id", "account_code", "name", "platform_code", "username", "password", "owner_user_id", "owner_name", "backup_contact", "current_viewers", "max_capacity", "engagement_rate", "lag_signal", "status", "stream_url", "warehouse_location", "shift_label", "created_at"],
    "supplier_offers": ["offer_id", "offer_code", "supplier_id", "product_id", "offer_title", "min_order_quantity", "unit_price", "discount_percent", "start_date", "end_date", "status", "notes"],
    "livestream_product_assignments": ["assignment_id", "account_id", "product_id", "assigned_by_user_id", "assigned_at"],
}

TABLE_RELATIONSHIPS = {
    "users": [],
    "platforms": [],
    "products": [],
    "suppliers": [],
    "livestream_accounts": [
        {"column": "platform_code", "references": "platforms.code"},
        {"column": "owner_user_id", "references": "users.user_id"},
    ],
    "supplier_offers": [
        {"column": "supplier_id", "references": "suppliers.supplier_id"},
        {"column": "product_id", "references": "products.product_id"},
    ],
    "livestream_product_assignments": [
        {"column": "account_id", "references": "livestream_accounts.account_id"},
        {"column": "product_id", "references": "products.product_id"},
        {"column": "assigned_by_user_id", "references": "users.user_id"},
    ],
}

TABLE_LOAD_ORDER = [
    "users",
    "platforms",
    "products",
    "suppliers",
    "livestream_accounts",
    "supplier_offers",
    "livestream_product_assignments",
]
TABLE_CLEAR_ORDER = [
    "livestream_product_assignments",
    "supplier_offers",
    "livestream_accounts",
    "suppliers",
    "products",
    "platforms",
    "users",
]

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    staff_code TEXT UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL,
    phone TEXT NOT NULL,
    department TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    phone TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    full_name TEXT NOT NULL,
    shipping_address TEXT NOT NULL,
    birth_year INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS platforms (
    platform_id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    category TEXT NOT NULL,
    region TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS livestream_accounts (
    account_id TEXT PRIMARY KEY,
    account_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    platform_code TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    owner_user_id TEXT,
    owner_name TEXT NOT NULL,
    backup_contact TEXT NOT NULL,
    current_viewers INTEGER NOT NULL,
    max_capacity INTEGER NOT NULL,
    engagement_rate REAL NOT NULL,
    lag_signal REAL NOT NULL,
    status TEXT NOT NULL,
    broadcast_status TEXT NOT NULL DEFAULT 'offline',
    live_started_at TEXT,
    last_heartbeat_at TEXT,
    stream_url TEXT NOT NULL,
    warehouse_location TEXT NOT NULL,
    shift_label TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (platform_code) REFERENCES platforms(code),
    FOREIGN KEY (owner_user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    brand TEXT NOT NULL,
    cost_price REAL NOT NULL,
    retail_price REAL NOT NULL,
    stock_quantity INTEGER NOT NULL,
    reorder_level INTEGER NOT NULL,
    unit TEXT NOT NULL,
    description TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id TEXT PRIMARY KEY,
    supplier_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    contact_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL,
    address TEXT NOT NULL,
    rating REAL NOT NULL,
    lead_time_days INTEGER NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS supplier_offers (
    offer_id TEXT PRIMARY KEY,
    offer_code TEXT NOT NULL UNIQUE,
    supplier_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    offer_title TEXT NOT NULL,
    min_order_quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    discount_percent REAL NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT NOT NULL,
    notes TEXT NOT NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS livestream_product_assignments (
    assignment_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    assigned_by_user_id TEXT,
    assigned_at TEXT NOT NULL,
    UNIQUE(account_id, product_id),
    FOREIGN KEY (account_id) REFERENCES livestream_accounts(account_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by_user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS livestream_product_offers (
    live_offer_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL UNIQUE,
    product_id TEXT NOT NULL,
    original_price REAL NOT NULL,
    live_price REAL NOT NULL,
    pinned_by_user_id TEXT,
    pinned_at TEXT NOT NULL,
    FOREIGN KEY (account_id) REFERENCES livestream_accounts(account_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    FOREIGN KEY (pinned_by_user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS customer_cart_items (
    cart_item_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    original_price REAL NOT NULL,
    added_at TEXT NOT NULL,
    UNIQUE(customer_id, account_id, product_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES livestream_accounts(account_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS customer_orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    total_amount REAL NOT NULL,
    shipping_address TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES livestream_accounts(account_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS customer_order_items (
    order_item_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    product_name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    original_price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES customer_orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS livestream_viewer_presence (
    presence_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    viewer_id TEXT NOT NULL,
    viewer_role TEXT NOT NULL,
    viewer_name TEXT NOT NULL,
    is_host INTEGER NOT NULL DEFAULT 0,
    is_live INTEGER NOT NULL DEFAULT 0,
    last_seen_at TEXT NOT NULL,
    UNIQUE(account_id, viewer_id),
    FOREIGN KEY (account_id) REFERENCES livestream_accounts(account_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_livestream_viewer_presence_account_id
ON livestream_viewer_presence(account_id);

CREATE INDEX IF NOT EXISTS idx_livestream_viewer_presence_last_seen
ON livestream_viewer_presence(last_seen_at);

CREATE TABLE IF NOT EXISTS livestream_comments (
    comment_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    content TEXT NOT NULL,
    intent TEXT NOT NULL,
    sentiment TEXT NOT NULL,
    priority TEXT NOT NULL,
    should_auto_message INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (account_id) REFERENCES livestream_accounts(account_id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_livestream_comments_account_created
ON livestream_comments(account_id, created_at);

CREATE TABLE IF NOT EXISTS conversation_messages (
    message_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    sender_id TEXT NOT NULL,
    sender_role TEXT NOT NULL,
    sender_name TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (account_id) REFERENCES livestream_accounts(account_id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_conversation_messages_account_customer_created
ON conversation_messages(account_id, customer_id, created_at);

CREATE TABLE IF NOT EXISTS ai_assistant_settings (
    settings_id TEXT PRIMARY KEY,
    is_enabled INTEGER NOT NULL DEFAULT 1,
    customer_reply_template TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if LEGACY_DB_PATH.exists() and not DB_PATH.exists():
        LEGACY_DB_PATH.replace(DB_PATH)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def save_json_record(table: str, record: dict) -> None:
    table_dir = TABLE_JSON_DIRS[table]
    table_dir.mkdir(parents=True, exist_ok=True)
    primary_key = TABLE_PRIMARY_KEYS[table]
    record_id = record[primary_key]
    file_path = table_dir / f"{record_id}.json"
    file_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")


def delete_json_record(table: str, record_id: str) -> None:
    file_path = TABLE_JSON_DIRS[table] / f"{record_id}.json"
    if file_path.exists():
        file_path.unlink()


def load_json_records(table: str) -> list[dict]:
    table_dir = TABLE_JSON_DIRS[table]
    if not table_dir.exists():
        return []
    records: list[dict] = []
    primary_key = TABLE_PRIMARY_KEYS[table]
    for file_path in sorted(table_dir.glob("*.json")):
        # Accept both UTF-8 and UTF-8 with BOM because seed files may be edited on Windows.
        record = json.loads(file_path.read_text(encoding="utf-8-sig"))
        if record.get(primary_key) != file_path.stem:
            raise ValueError(
                f"JSON file {file_path.name} must match primary key {primary_key}={record.get(primary_key)}"
            )
        records.append(record)
    return records


def should_seed_from_json(connection: sqlite3.Connection) -> bool:
    for table in TABLE_LOAD_ORDER:
        total_rows = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if total_rows:
            return False
    return True


def get_existing_tables(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()
    return {row[0] for row in rows}


def insert_records(connection: sqlite3.Connection, table: str, records: list[dict]) -> None:
    if not records:
        return
    relationships = TABLE_RELATIONSHIPS.get(table, [])
    valid_records: list[dict] = []
    for record in records:
        is_valid = True
        for relationship in relationships:
            value = record.get(relationship["column"])
            if value is None:
                continue
            referenced_table, referenced_column = relationship["references"].split(".", maxsplit=1)
            referenced_row = connection.execute(
                f"SELECT 1 FROM {referenced_table} WHERE {referenced_column} = ? LIMIT 1",
                (value,),
            ).fetchone()
            if not referenced_row:
                is_valid = False
                break
        if is_valid:
            valid_records.append(record)
    if not valid_records:
        return
    columns = TABLE_INSERT_COLUMNS[table]
    placeholders = ", ".join("?" for _ in columns)
    # Seed data is shared across multiple services and startup can happen in parallel,
    # so inserts must be idempotent to avoid crashing on existing unique values.
    query = f"INSERT OR IGNORE INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    values = [tuple(record.get(column) for column in columns) for record in valid_records]
    connection.executemany(query, values)


def insert_missing_seed_records(connection: sqlite3.Connection, table: str) -> None:
    primary_key = TABLE_PRIMARY_KEYS[table]
    existing_ids = {
        row[0]
        for row in connection.execute(f"SELECT {primary_key} FROM {table}").fetchall()
    }
    missing_records = [
        record
        for record in load_json_records(table)
        if record.get(primary_key) not in existing_ids
    ]
    insert_records(connection, table, missing_records)


def ensure_schema_migrations(connection: sqlite3.Connection) -> None:
    user_columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(users)").fetchall()
    }
    if "staff_code" not in user_columns:
        connection.execute("ALTER TABLE users ADD COLUMN staff_code TEXT")
    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_staff_code
        ON users(staff_code)
        WHERE staff_code IS NOT NULL
        """
    )

    livestream_columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(livestream_accounts)").fetchall()
    }
    if "password" not in livestream_columns:
        connection.execute(
            "ALTER TABLE livestream_accounts ADD COLUMN password TEXT NOT NULL DEFAULT 'live123'"
        )
    if "broadcast_status" not in livestream_columns:
        connection.execute(
            "ALTER TABLE livestream_accounts ADD COLUMN broadcast_status TEXT NOT NULL DEFAULT 'offline'"
        )
    if "live_started_at" not in livestream_columns:
        connection.execute("ALTER TABLE livestream_accounts ADD COLUMN live_started_at TEXT")
    if "last_heartbeat_at" not in livestream_columns:
        connection.execute("ALTER TABLE livestream_accounts ADD COLUMN last_heartbeat_at TEXT")

    ai_columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(ai_assistant_settings)").fetchall()
    }
    if ai_columns and "updated_at" not in ai_columns:
        connection.execute("ALTER TABLE ai_assistant_settings ADD COLUMN updated_at TEXT")


def ensure_default_ai_settings(connection: sqlite3.Connection) -> None:
    existing = connection.execute(
        "SELECT settings_id FROM ai_assistant_settings WHERE settings_id = 'default'"
    ).fetchone()
    if existing:
        return
    updated_at = connection.execute("SELECT datetime('now')").fetchone()[0]
    connection.execute(
        """
        INSERT INTO ai_assistant_settings (
            settings_id,
            is_enabled,
            customer_reply_template,
            updated_at
        ) VALUES (?, ?, ?, ?)
        """,
        (
            "default",
            1,
            "Chào {customer_name}, SmartLive thấy bạn đang quan tâm sản phẩm trong phiên live. Shop đã mở hội thoại để nhân viên hỗ trợ bạn nhanh hơn.",
            updated_at,
        ),
    )


def ensure_default_demo_customers(connection: sqlite3.Connection) -> None:
    demo_customers = [
        {
            "customer_id": "customer-0901234567",
            "phone": "0901234567",
            "email": "khach1@smartlive.vn",
            "password": "123456",
            "full_name": "Nguyễn Thị An",
            "shipping_address": "Quận 7, TP.HCM",
            "birth_year": 1998,
        },
        {
            "customer_id": "customer-0912345678",
            "phone": "0912345678",
            "email": "khach2@smartlive.vn",
            "password": "123456",
            "full_name": "Trần Minh Khoa",
            "shipping_address": "Thủ Đức, TP.HCM",
            "birth_year": 1996,
        },
    ]
    for customer in demo_customers:
        existing = connection.execute(
            "SELECT customer_id FROM customers WHERE customer_id = ? OR phone = ? OR email = ?",
            (customer["customer_id"], customer["phone"], customer["email"]),
        ).fetchone()
        if existing:
            continue
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
                customer["customer_id"],
                customer["phone"],
                customer["email"],
                customer["password"],
                customer["full_name"],
                customer["shipping_address"],
                customer["birth_year"],
                "active",
                connection.execute("SELECT datetime('now')").fetchone()[0],
            ),
        )


def initialize_database() -> None:
    with get_connection() as connection:
        existing_tables = get_existing_tables(connection)
        connection.executescript(SCHEMA_SQL)
        ensure_schema_migrations(connection)
        ensure_default_ai_settings(connection)
        ensure_default_demo_customers(connection)
        if not existing_tables.intersection(TABLE_LOAD_ORDER):
            for table in TABLE_LOAD_ORDER:
                insert_records(connection, table, load_json_records(table))
        else:
            for table in TABLE_LOAD_ORDER:
                if table not in existing_tables:
                    insert_records(connection, table, load_json_records(table))
                else:
                    insert_missing_seed_records(connection, table)
        connection.commit()
