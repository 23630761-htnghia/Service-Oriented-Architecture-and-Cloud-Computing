from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = DATA_DIR / "account_management.db"

TABLE_PRIMARY_KEYS = {
    "users": "user_id",
    "platforms": "platform_id",
    "products": "product_id",
    "suppliers": "supplier_id",
    "livestream_accounts": "account_id",
    "supplier_offers": "offer_id",
}

TABLE_JSON_DIRS = {table: DATA_DIR / table for table in TABLE_PRIMARY_KEYS}

TABLE_INSERT_COLUMNS = {
    "users": ["user_id", "email", "password", "full_name", "role", "phone", "department", "status", "created_at", "last_login_at"],
    "platforms": ["platform_id", "code", "display_name", "category", "region", "is_active"],
    "products": ["product_id", "sku", "name", "category", "brand", "cost_price", "retail_price", "stock_quantity", "reorder_level", "unit", "description", "is_active"],
    "suppliers": ["supplier_id", "supplier_code", "name", "contact_name", "phone", "email", "address", "rating", "lead_time_days", "status"],
    "livestream_accounts": ["account_id", "account_code", "name", "platform_code", "username", "owner_user_id", "owner_name", "backup_contact", "current_viewers", "max_capacity", "engagement_rate", "lag_signal", "status", "stream_url", "warehouse_location", "shift_label", "created_at"],
    "supplier_offers": ["offer_id", "offer_code", "supplier_id", "product_id", "offer_title", "min_order_quantity", "unit_price", "discount_percent", "start_date", "end_date", "status", "notes"],
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
}

TABLE_LOAD_ORDER = ["users", "platforms", "products", "suppliers", "livestream_accounts", "supplier_offers"]
TABLE_CLEAR_ORDER = ["supplier_offers", "livestream_accounts", "suppliers", "products", "platforms", "users"]

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
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
    owner_user_id TEXT,
    owner_name TEXT NOT NULL,
    backup_contact TEXT NOT NULL,
    current_viewers INTEGER NOT NULL,
    max_capacity INTEGER NOT NULL,
    engagement_rate REAL NOT NULL,
    lag_signal REAL NOT NULL,
    status TEXT NOT NULL,
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
"""


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
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


def load_json_records(table: str) -> list[dict]:
    table_dir = TABLE_JSON_DIRS[table]
    if not table_dir.exists():
        return []
    records: list[dict] = []
    primary_key = TABLE_PRIMARY_KEYS[table]
    for file_path in sorted(table_dir.glob("*.json")):
        record = json.loads(file_path.read_text(encoding="utf-8"))
        if record.get(primary_key) != file_path.stem:
            raise ValueError(
                f"JSON file {file_path.name} must match primary key {primary_key}={record.get(primary_key)}"
            )
        records.append(record)
    return records


def clear_existing_data(connection: sqlite3.Connection) -> None:
    for table in TABLE_CLEAR_ORDER:
        connection.execute(f"DELETE FROM {table}")


def insert_records(connection: sqlite3.Connection, table: str, records: list[dict]) -> None:
    if not records:
        return
    columns = TABLE_INSERT_COLUMNS[table]
    placeholders = ", ".join("?" for _ in columns)
    query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    values = [tuple(record.get(column) for column in columns) for record in records]
    connection.executemany(query, values)


def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(SCHEMA_SQL)
        clear_existing_data(connection)
        for table in TABLE_LOAD_ORDER:
            insert_records(connection, table, load_json_records(table))
        connection.commit()
