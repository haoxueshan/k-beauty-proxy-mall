import os

from settings import get_settings


def test_settings_supports_comma_separated_origins_and_hosts() -> None:
    original = {
        "ALLOWED_ORIGINS": os.environ.get("ALLOWED_ORIGINS"),
        "TRUSTED_HOSTS": os.environ.get("TRUSTED_HOSTS"),
        "PORT_AUTO_FALLBACK": os.environ.get("PORT_AUTO_FALLBACK"),
    }
    try:
        os.environ["ALLOWED_ORIGINS"] = "https://mall.example.com, https://www.mall.example.com"
        os.environ["TRUSTED_HOSTS"] = "mall.example.com,www.mall.example.com"
        os.environ["PORT_AUTO_FALLBACK"] = "false"
        get_settings.cache_clear()

        settings = get_settings()

        assert settings.allowed_origins == [
            "https://mall.example.com",
            "https://www.mall.example.com",
        ]
        assert settings.trusted_hosts == [
            "mall.example.com",
            "www.mall.example.com",
        ]
        assert settings.port_auto_fallback is False
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        get_settings.cache_clear()
