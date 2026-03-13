"""
Configuration loader.

Settings are split into two layers:
  1. config/settings.yaml  — non-secret config (markets, thresholds, URLs)
                             safe to version-control
  2. .env                  — secrets (API keys, tokens)
                             in .gitignore, never committed

Env vars always win over yaml values. This means you can also override
any setting at runtime by setting an env var (useful for CI/containers).
"""

import os
from pathlib import Path

import yaml

_CONFIG = None
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Map: env var name → (yaml path as tuple of keys)
_SECRET_ENV_VARS = {
    "BINANCE_API_KEY":     ("binance", "api_key"),
    "BINANCE_API_SECRET":  ("binance", "api_secret"),
    "NOONES_API_KEY":      ("noones", "api_key"),
    "NOONES_API_SECRET":   ("noones", "api_secret"),
    "TELEGRAM_BOT_TOKEN":  ("telegram", "bot_token"),
    "TELEGRAM_CHAT_ID":    ("telegram", "chat_id"),
    "CEREBRAS_API_KEY":    ("intelligence", "api_key"),
}


def _load_dotenv(env_path: Path):
    """Minimal .env loader — no dependency on python-dotenv."""
    if not env_path.exists():
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and val and key not in os.environ:
                os.environ[key] = val


def _set_nested(d: dict, keys: tuple, value: str):
    """Set a nested dict value by key path, creating intermediate dicts."""
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value


def load_config(path: str | None = None) -> dict:
    """Load and cache configuration. Secrets from .env overlay yaml."""
    global _CONFIG
    if _CONFIG is not None and path is None:
        return _CONFIG

    # Load .env first so env vars are available
    _load_dotenv(_PROJECT_ROOT / ".env")

    if path is None:
        path = _PROJECT_ROOT / "config" / "settings.yaml"

    with open(path) as f:
        _CONFIG = yaml.safe_load(f)

    # Overlay secrets from environment
    for env_var, key_path in _SECRET_ENV_VARS.items():
        value = os.environ.get(env_var)
        if value:
            _set_nested(_CONFIG, key_path, value)

    # Resolve relative paths to absolute
    db_path = _CONFIG.get("database", {}).get("path", "db/trades.db")
    if not os.path.isabs(db_path):
        _CONFIG["database"]["path"] = str(_PROJECT_ROOT / db_path)

    log_file = _CONFIG.get("logging", {}).get("file", "logs/cryptodistro.log")
    if not os.path.isabs(log_file):
        _CONFIG["logging"]["file"] = str(_PROJECT_ROOT / log_file)

    return _CONFIG


def get_config() -> dict:
    """Return the cached config, loading if needed."""
    if _CONFIG is None:
        return load_config()
    return _CONFIG
