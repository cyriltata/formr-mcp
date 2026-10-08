import logging
import sys
from pathlib import Path

import uvicorn
from mcp.server.transport_security import TransportSecuritySettings

from formr_mcp.app import ServiceGate
from formr_mcp.client import configure
from formr_mcp.config import Settings, load_local_env, load_settings
from formr_mcp.server import build_server

# 12MB file bytes become ~16MB of base64, plus the JSON envelope.
MAX_REQUEST_BODY_BYTES = 18 * 1024 * 1024
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def main() -> None:
    _serve(reload=False)


def dev() -> None:
    """Local process. Restarts when a file under formr_mcp/ changes."""
    _serve(reload=True)


def create_app() -> ServiceGate:
    """Uvicorn calls this again after each reload."""
    load_local_env()
    return build_app(load_settings())


def _serve(reload: bool) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    load_local_env()
    try:
        settings = load_settings()
    except ValueError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(2) from exc
    _log_startup(settings)
    options = {
        "host": settings.host,
        "port": settings.port,
        "log_level": "info",
        "proxy_headers": False,
        "server_header": False,
        "timeout_graceful_shutdown": 10,
    }
    if reload:
        logging.info("watching %s for changes", Path(__file__).resolve().parent)
        uvicorn.run(
            "formr_mcp.main:create_app",
            factory=True,
            reload=True,
            reload_dirs=[str(Path(__file__).resolve().parent)],
            **options,
        )
        return
    uvicorn.run(build_app(settings), reload=False, **options)


def build_app(settings: Settings) -> ServiceGate:
    configure(settings)
    app = build_server().streamable_http_app(
        stateless_http=True,
        json_response=True,
        host=settings.host,
        transport_security=_transport_security(settings),
        max_request_body_size=MAX_REQUEST_BODY_BYTES,
    )
    return ServiceGate(app, settings)


def _transport_security(settings: Settings) -> TransportSecuritySettings | None:
    """Keep DNS-rebinding checks on when Docker binds every interface.

    The SDK enables those checks only for a loopback bind. 0.0.0.0 would otherwise accept any Host.
    """
    if settings.host in LOOPBACK_HOSTS:
        return None
    origins = [host if "://" in host else f"http://{host}" for host in settings.allowed_hosts]
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=list(settings.allowed_hosts),
        allowed_origins=origins,
    )


def _log_startup(settings: Settings) -> None:
    logging.info("listening on %s:%s", settings.host, settings.port)
    if settings.allowed_origins:
        logging.info("formr instances allowed: %s", ", ".join(settings.allowed_origins))
    else:
        logging.warning("FORMR_ALLOWED_INSTANCE_URLS is unset; any http(s) instance URL is accepted")
    if settings.host not in LOOPBACK_HOSTS:
        logging.info("allowed Host headers: %s", ", ".join(settings.allowed_hosts))


if __name__ == "__main__":
    main()
