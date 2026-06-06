import os
import json
from urllib import error, parse, request

from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()


def get_supabase_settings() -> dict[str, str | None]:
    return {
        "url": os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
        "anon_key": os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY"),
        "service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    }


def require_supabase_settings() -> dict[str, str]:
    settings = get_supabase_settings()
    url = settings["url"]
    service_role_key = settings["service_role_key"]

    if not url or not service_role_key:
        raise HTTPException(
            status_code=500,
            detail="Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.",
        )

    if service_role_key.startswith("sb_publishable_"):
        raise HTTPException(
            status_code=500,
            detail=(
                "Invalid Supabase backend key: SUPABASE_SERVICE_ROLE_KEY is currently a publishable key. "
                "Use the real service role key for server-side writes, or redesign auth/data access around "
                "Supabase Auth + RLS."
            ),
        )

    return {
        "url": url.rstrip("/"),
        "service_role_key": service_role_key,
    }


def _build_headers(extra_headers: dict[str, str] | None = None) -> dict[str, str]:
    settings = require_supabase_settings()
    headers = {
        "apikey": settings["service_role_key"],
        "Authorization": f"Bearer {settings['service_role_key']}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    return headers


def _build_url(path: str, query: dict[str, str] | None = None) -> str:
    settings = require_supabase_settings()
    encoded_query = parse.urlencode(query or {})
    suffix = f"?{encoded_query}" if encoded_query else ""
    return f"{settings['url']}{path}{suffix}"


def _decode_response(response_body: bytes):
    if not response_body:
        return None
    return json.loads(response_body.decode("utf-8"))


def _request_json(
    method: str,
    path: str,
    *,
    query: dict[str, str] | None = None,
    payload: dict | list | None = None,
    headers: dict[str, str] | None = None,
):
    request_headers = _build_headers(headers)
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    http_request = request.Request(
        _build_url(path, query),
        data=body,
        headers=request_headers,
        method=method,
    )

    try:
        with request.urlopen(http_request) as response:
            return _decode_response(response.read())
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8")
        try:
            parsed = json.loads(detail)
            message = parsed.get("message") or parsed.get("error") or detail
        except json.JSONDecodeError:
            message = detail or exc.reason
        raise HTTPException(status_code=exc.code, detail=message) from exc
    except error.URLError as exc:
        raise HTTPException(status_code=502, detail=f"Supabase request failed: {exc.reason}") from exc


def select_rows(
    table: str,
    *,
    columns: str = "*",
    filters: dict[str, str] | None = None,
    order: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    query = {"select": columns}
    if filters:
        query.update(filters)
    if order:
        query["order"] = order
    if limit is not None:
        query["limit"] = str(limit)
    response = _request_json("GET", f"/rest/v1/{table}", query=query)
    return response or []


def insert_rows(table: str, payload: dict | list[dict]) -> list[dict]:
    response = _request_json(
        "POST",
        f"/rest/v1/{table}",
        payload=payload,
        headers={"Prefer": "return=representation"},
    )
    return response or []


def update_rows(table: str, *, filters: dict[str, str], payload: dict) -> list[dict]:
    response = _request_json(
        "PATCH",
        f"/rest/v1/{table}",
        query=filters,
        payload=payload,
        headers={"Prefer": "return=representation"},
    )
    return response or []


def delete_rows(table: str, *, filters: dict[str, str]) -> list[dict]:
    response = _request_json(
        "DELETE",
        f"/rest/v1/{table}",
        query=filters,
        headers={"Prefer": "return=representation"},
    )
    return response or []
