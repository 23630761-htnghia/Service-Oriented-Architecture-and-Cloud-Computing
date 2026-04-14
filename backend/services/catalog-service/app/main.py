from __future__ import annotations

import re

from fastapi import FastAPI, HTTPException

from app.database import delete_json_record, get_connection, initialize_database, save_json_record
from app.schemas import (
    HealthResponse,
    ProductCreate,
    ProductDeleteResponse,
    ProductItem,
    ProductUpdate,
    Supplier,
    SupplierCreate,
    SupplierDeleteResponse,
    SupplierOffer,
    SupplierUpdate,
)

app = FastAPI(
    title="Catalog Service",
    version="0.4.0",
    description="Catalog, supplier and offer service for livestream management.",
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
    return {**product, "is_active": bool(product["is_active"])}


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


@app.get("/")
def root():
    return {
        "service": "catalog-service",
        "status": "ok",
        "message": "Catalog Service is running.",
        "docs_url": "/docs",
        "health_url": "/health",
        "main_routes": ["/products", "/suppliers", "/supplier-offers"],
    }


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="catalog-service")


@app.get("/products", response_model=list[ProductItem])
def list_products() -> list[ProductItem]:
    return list_products_data()


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
        connection.execute("DELETE FROM supplier_offers WHERE supplier_id = ?", (supplier_id,))
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
