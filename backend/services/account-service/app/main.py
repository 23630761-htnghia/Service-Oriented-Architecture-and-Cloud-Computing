from __future__ import annotations

import re

from fastapi import FastAPI, HTTPException

from app.database import delete_json_record, get_connection, initialize_database, save_json_record
from app.schemas import (
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
