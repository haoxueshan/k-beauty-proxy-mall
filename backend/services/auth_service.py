import hashlib
import hmac
import secrets
from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException

from db.supabase_client import delete_rows, insert_rows, select_rows, update_rows
from schemas import LoginRequest, RegisterRequest, UserPublic


def _normalize_identifier(value: str) -> str:
    return value.strip().lower()


def _hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return digest.hex()


def _normalize_role(role: str | None, is_admin: bool | None = False) -> str:
    if role in {"user", "admin", "super_admin"}:
        return role
    return "admin" if is_admin else "user"


def _serialize_user(record: dict) -> UserPublic:
    role = _normalize_role(record.get("role"), bool(record.get("is_admin")))
    return UserPublic(
        id=record["id"],
        email=record["email"],
        name=record["name"],
        phone=record.get("phone"),
        role=role,
        is_admin=role in {"admin", "super_admin"},
        created_at=datetime.fromisoformat(record["created_at"]),
    )


def _sync_profile(record: dict) -> None:
    try:
        select_rows("profiles", columns="id", limit=1)
    except HTTPException:
        return

    payload = {
        "id": record["id"],
        "email": record["email"],
        "role": _normalize_role(record.get("role"), bool(record.get("is_admin"))),
        "created_at": record.get("created_at") or datetime.utcnow().isoformat(),
    }
    existing_profiles = select_rows("profiles", columns="id", filters={"id": f"eq.{record['id']}"}, limit=1)
    if existing_profiles:
        update_rows("profiles", filters={"id": f"eq.{record['id']}"}, payload=payload)
        return
    insert_rows("profiles", payload)


def register_user(payload: RegisterRequest) -> tuple[str, UserPublic]:
    email = _normalize_identifier(payload.email)

    existing_users = select_rows("users", columns="id", filters={"email": f"eq.{email}"}, limit=1)
    if existing_users:
        raise HTTPException(status_code=409, detail="Email already registered")

    salt = secrets.token_hex(16)
    user_id = str(uuid4())
    user_record = {
        "id": user_id,
        "email": email,
        "name": payload.name.strip(),
        "phone": payload.phone.strip() if payload.phone else None,
        "role": "user",
        "is_admin": False,
        "password_salt": salt,
        "password_hash": _hash_password(payload.password, salt),
        "created_at": datetime.utcnow().isoformat(),
    }
    created_users = insert_rows("users", user_record)
    created_user = created_users[0]
    _sync_profile(created_user)

    token = secrets.token_urlsafe(32)
    insert_rows(
        "auth_sessions",
        {
            "id": str(uuid4()),
            "token": token,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
        },
    )
    return token, _serialize_user(created_user)


def login_user(payload: LoginRequest) -> tuple[str, UserPublic]:
    identifier = _normalize_identifier(payload.email)
    users = select_rows(
        "users",
        columns="*",
        filters={"email": f"eq.{identifier}"},
        limit=1,
    )
    if not users:
        users = select_rows(
            "users",
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

    token = secrets.token_urlsafe(32)
    insert_rows(
        "auth_sessions",
        {
            "id": str(uuid4()),
            "token": token,
            "user_id": user_record["id"],
            "created_at": datetime.utcnow().isoformat(),
        },
    )
    _sync_profile(user_record)
    return token, _serialize_user(user_record)


def get_user_by_token(token: str) -> UserPublic:
    sessions = select_rows("auth_sessions", columns="token,user_id", filters={"token": f"eq.{token}"}, limit=1)
    if not sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    session = sessions[0]

    users = select_rows(
        "users",
        columns="*",
        filters={"id": f"eq.{session['user_id']}"},
        limit=1,
    )
    if not users:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return _serialize_user(users[0])


def logout_user(token: str) -> None:
    delete_rows("auth_sessions", filters={"token": f"eq.{token}"})
