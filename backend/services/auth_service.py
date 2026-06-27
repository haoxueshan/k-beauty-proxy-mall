import hashlib
import hmac
import re
import secrets
from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException

from db.supabase_client import delete_rows, insert_rows, select_rows, update_rows
from schemas import LoginRequest, PasswordResetRequest, RegisterRequest, UserPublic

CUSTOMER_TABLE = "users"
ADMIN_TABLE = "admin_users"
CUSTOMER_SESSION_TABLE = "auth_sessions"
ADMIN_SESSION_TABLE = "admin_auth_sessions"


def _normalize_identifier(value: str) -> str:
    return value.strip().lower()


def _hash_password(password: str, salt: str) -> str:
    # 每个用户独立 salt，登录时重新计算 hash 后用恒定时间比较，避免明文存储密码。
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return digest.hex()


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.utcnow()
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _phone_digits(value: str | None) -> str:
    return "".join(re.findall(r"\d", value or ""))


def _test_verification_code(phone: str | None) -> str:
    # MVP 阶段用手机号后四位模拟验证码，后续接短信服务时只替换这里和校验逻辑。
    digits = _phone_digits(phone)
    if len(digits) < 4:
        raise HTTPException(status_code=400, detail="Phone number must contain at least 4 digits")
    return digits[-4:]


def _assert_verification_code(phone: str | None, code: str | None) -> None:
    expected_code = _test_verification_code(phone)
    if (code or "").strip() != expected_code:
        raise HTTPException(status_code=400, detail="Invalid verification code")


def _serialize_user(record: dict, *, default_role: str = "user", force_admin: bool = False) -> UserPublic:
    role = record.get("role") or default_role
    if force_admin and role == "user":
        role = "admin"
    is_admin = role in {"admin", "super_admin"} or bool(record.get("is_admin"))
    return UserPublic(
        id=record["id"],
        email=record["email"],
        name=record["name"],
        phone=record.get("phone"),
        role=role if role in {"user", "admin", "super_admin"} else default_role,
        is_admin=is_admin,
        created_at=_parse_datetime(record.get("created_at")),
    )


def _sync_profile(record: dict) -> None:
    # 兼容早期 Supabase profiles 表：存在就同步，不存在则安静跳过。
    try:
        select_rows("profiles", columns="id", limit=1)
    except HTTPException:
        return

    payload = {
        "id": record["id"],
        "email": record["email"],
        "role": "user",
        "created_at": record.get("created_at") or datetime.utcnow().isoformat(),
    }
    existing_profiles = select_rows("profiles", columns="id", filters={"id": f"eq.{record['id']}"}, limit=1)
    if existing_profiles:
        update_rows("profiles", filters={"id": f"eq.{record['id']}"}, payload=payload)
        return
    insert_rows("profiles", payload)


def _create_session(table: str, account_id: str) -> str:
    # 用户和管理员使用不同 session 表，避免普通用户 token 误读后台身份。
    token = secrets.token_urlsafe(32)
    insert_rows(
        table,
        {
            "id": str(uuid4()),
            "token": token,
            "user_id": account_id,
            "created_at": datetime.utcnow().isoformat(),
        },
    )
    return token


def register_user(payload: RegisterRequest) -> tuple[str, UserPublic]:
    email = _normalize_identifier(payload.email)
    phone = payload.phone.strip()
    _assert_verification_code(phone, payload.verification_code)

    existing_customers = select_rows(CUSTOMER_TABLE, columns="id", filters={"email": f"eq.{email}"}, limit=1)
    if existing_customers:
        raise HTTPException(status_code=409, detail="Email already registered")

    existing_admins = select_rows(ADMIN_TABLE, columns="id", filters={"email": f"eq.{email}"}, limit=1)
    if existing_admins:
        raise HTTPException(status_code=409, detail="Email is reserved for an admin account")

    salt = secrets.token_hex(16)
    user_id = str(uuid4())
    user_record = {
        "id": user_id,
        "email": email,
        "name": payload.name.strip(),
        "phone": phone,
        "role": "user",
        "is_admin": False,
        "password_salt": salt,
        "password_hash": _hash_password(payload.password, salt),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    created_users = insert_rows(CUSTOMER_TABLE, user_record)
    created_user = created_users[0]
    _sync_profile(created_user)

    token = _create_session(CUSTOMER_SESSION_TABLE, user_id)
    return token, _serialize_user(created_user)


def login_user(payload: LoginRequest) -> tuple[str, UserPublic]:
    identifier = _normalize_identifier(payload.email)

    # 管理员优先从独立表登录，后台订单接口会依赖 role 做权限判断。
    admins = select_rows(
        ADMIN_TABLE,
        columns="*",
        filters={"email": f"eq.{identifier}"},
        limit=1,
    )
    if admins:
        admin_record = admins[0]
        expected_hash = _hash_password(payload.password, admin_record["password_salt"])
        if not hmac.compare_digest(expected_hash, admin_record["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        token = _create_session(ADMIN_SESSION_TABLE, admin_record["id"])
        return token, _serialize_user(admin_record, default_role="admin", force_admin=True)

    users = select_rows(
        CUSTOMER_TABLE,
        columns="*",
        filters={"email": f"eq.{identifier}"},
        limit=1,
    )
    if not users:
        users = select_rows(
            CUSTOMER_TABLE,
            columns="*",
            filters={"name": f"eq.{identifier}"},
            limit=1,
        )
    if not users:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_record = users[0]
    expected_hash = _hash_password(payload.password, user_record["password_salt"])
    if not hmac.compare_digest(expected_hash, user_record["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = _create_session(CUSTOMER_SESSION_TABLE, user_record["id"])
    _sync_profile(user_record)
    return token, _serialize_user(user_record)


def reset_user_password(payload: PasswordResetRequest) -> None:
    # 重置密码后清理旧 session，防止旧设备继续保持登录态。
    email = _normalize_identifier(payload.email)
    phone = payload.phone.strip()
    _assert_verification_code(phone, payload.verification_code)

    users = select_rows(CUSTOMER_TABLE, columns="*", filters={"email": f"eq.{email}"}, limit=1)
    if not users:
        raise HTTPException(status_code=404, detail="Customer account not found")

    user_record = users[0]
    if _phone_digits(user_record.get("phone"))[-4:] != _phone_digits(phone)[-4:]:
        raise HTTPException(status_code=400, detail="Phone number does not match this account")

    salt = secrets.token_hex(16)
    update_rows(
        CUSTOMER_TABLE,
        filters={"id": f"eq.{user_record['id']}"},
        payload={
            "password_salt": salt,
            "password_hash": _hash_password(payload.new_password, salt),
            "updated_at": datetime.utcnow().isoformat(),
        },
    )
    delete_rows(CUSTOMER_SESSION_TABLE, filters={"user_id": f"eq.{user_record['id']}"})


def get_user_by_token(token: str) -> UserPublic:
    admin_sessions = select_rows(ADMIN_SESSION_TABLE, columns="token,user_id", filters={"token": f"eq.{token}"}, limit=1)
    if admin_sessions:
        admin_record_id = admin_sessions[0]["user_id"]
        admins = select_rows(ADMIN_TABLE, columns="*", filters={"id": f"eq.{admin_record_id}"}, limit=1)
        if not admins:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        return _serialize_user(admins[0], default_role="admin", force_admin=True)

    sessions = select_rows(CUSTOMER_SESSION_TABLE, columns="token,user_id", filters={"token": f"eq.{token}"}, limit=1)
    if not sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    user_id = sessions[0]["user_id"]
    users = select_rows(
        CUSTOMER_TABLE,
        columns="*",
        filters={"id": f"eq.{user_id}"},
        limit=1,
    )
    if not users:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return _serialize_user(users[0])


def logout_user(token: str) -> None:
    delete_rows(ADMIN_SESSION_TABLE, filters={"token": f"eq.{token}"})
    delete_rows(CUSTOMER_SESSION_TABLE, filters={"token": f"eq.{token}"})
