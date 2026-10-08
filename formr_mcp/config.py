import os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, Field

INSTANCE_HEADER_NAME = "X-Formr-Instance-Url"
INSTANCE_HEADER = INSTANCE_HEADER_NAME.lower()
# Used when the process listens on every interface. Loopback binds keep the SDK default.
DEFAULT_ALLOWED_HOSTS = ("127.0.0.1:*", "localhost:*", "[::1]:*", "formr-mcp:*")


class InstanceNotAllowed(PermissionError):
    pass


class Settings(BaseModel):
    """Process configuration. The formr user and instance arrive per request."""

    host: str = "127.0.0.1"
    port: int = Field(default=3001, ge=1, le=65535)
    service_token: str = Field(min_length=1)
    # Empty means every well-formed http(s) instance URL is accepted.
    allowed_origins: tuple[str, ...] = ()
    allowed_hosts: tuple[str, ...] = DEFAULT_ALLOWED_HOSTS

    def resolve_instance(self, raw: str) -> str:
        origin = normalize_instance_url(raw)
        if self.allowed_origins and origin not in self.allowed_origins:
            raise InstanceNotAllowed(f"formr instance is not allowed: {origin}")
        return origin


def load_local_env() -> None:
    """Copy unset variables from the project .env. Existing environment wins."""
    path = _dotenv_path()
    if path is None:
        return
    for line in path.read_text().splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = value.strip().strip('"').strip("'")


def _dotenv_path() -> Path | None:
    candidates = (Path.cwd() / ".env", Path(__file__).resolve().parent.parent / ".env")
    for path in candidates:
        if path.is_file():
            return path
    return None


def load_settings(env: dict[str, str] | None = None) -> Settings:
    source = os.environ if env is None else env
    port = source.get("FORMR_MCP_PORT", "3001")
    return Settings(
        host=source.get("FORMR_MCP_HOST", "127.0.0.1"),
        port=int(port),
        service_token=_required(source, "FORMR_MCP_SERVICE_TOKEN"),
        allowed_origins=_allowed_origins(source),
        allowed_hosts=_allowed_hosts(source),
    )


def normalize_instance_url(raw: str) -> str:
    """Return scheme://host[:port] for a formr instance base URL."""
    text = raw.strip()
    if not text:
        raise ValueError(f"{INSTANCE_HEADER_NAME} is required")
    parts = urlsplit(text)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError(f"{INSTANCE_HEADER_NAME} must be an http(s) URL")
    if parts.username or parts.password:
        raise ValueError(f"{INSTANCE_HEADER_NAME} must not contain credentials")
    path = parts.path.rstrip("/")
    if path.endswith("/api/v1"):
        path = path[: -len("/api/v1")].rstrip("/")
    if path not in {"", "/"}:
        raise ValueError(f"{INSTANCE_HEADER_NAME} must be the instance origin, not a path")
    host = parts.hostname
    if ":" in host:
        host = f"[{host}]"
    port = parts.port
    default_port = (parts.scheme == "http" and port == 80) or (parts.scheme == "https" and port == 443)
    netloc = host if port is None or default_port else f"{host}:{port}"
    return urlunsplit((parts.scheme, netloc, "", "", ""))


def _allowed_hosts(env: dict[str, str]) -> tuple[str, ...]:
    raw = env.get("FORMR_MCP_ALLOWED_HOSTS", "").strip()
    if not raw:
        return DEFAULT_ALLOWED_HOSTS
    hosts = [piece.strip() for piece in raw.split(",") if piece.strip()]
    return tuple(dict.fromkeys(hosts))


def _allowed_origins(env: dict[str, str]) -> tuple[str, ...]:
    raw = env.get("FORMR_ALLOWED_INSTANCE_URLS", "").strip()
    if not raw:
        return ()
    origins: list[str] = []
    for piece in raw.split(","):
        piece = piece.strip()
        if piece:
            origins.append(normalize_instance_url(piece))
    return tuple(dict.fromkeys(origins))


def _required(env: dict[str, str], name: str) -> str:
    value = env.get(name, "").strip()
    if not value:
        raise ValueError(f"{name} is required")
    return value
