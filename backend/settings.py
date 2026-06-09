import logging
import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _env_flag(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str, default: list[str]) -> list[str]:
    raw_value = os.getenv(name)
    if raw_value is None:
        return list(default)

    normalized = raw_value.strip()
    if not normalized:
        return list(default)
    if normalized == "*":
        return ["*"]
    return [item.strip() for item in normalized.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    app_env: str
    log_level: str
    host: str
    port: int
    uvicorn_reload: bool
    port_auto_fallback: bool
    allowed_origins: list[str]
    trusted_hosts: list[str]

    @property
    def allow_all_origins(self) -> bool:
        return self.allowed_origins == ["*"]

    @property
    def allow_all_hosts(self) -> bool:
        return self.trusted_hosts == ["*"]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "olive-young-proxy-api"),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        app_env=os.getenv("APP_ENV", "development").strip().lower(),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        host=os.getenv("HOST", "127.0.0.1").strip(),
        port=int(os.getenv("PORT", os.getenv("BACKEND_PORT", "8000"))),
        uvicorn_reload=_env_flag("UVICORN_RELOAD", default=False),
        port_auto_fallback=_env_flag("PORT_AUTO_FALLBACK", default=False),
        allowed_origins=_env_list("ALLOWED_ORIGINS", ["*"]),
        trusted_hosts=_env_list("TRUSTED_HOSTS", ["*"]),
    )


def configure_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
