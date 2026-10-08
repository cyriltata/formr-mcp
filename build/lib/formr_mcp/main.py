import logging
import sys

import uvicorn

from formr_mcp.app import ServiceGate
from formr_mcp.client import configure
from formr_mcp.config import load_settings
from formr_mcp.server import build_server


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    try:
        settings = load_settings()
    except ValueError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(2) from exc
    configure(settings)
    app = build_server().streamable_http_app(
        stateless_http=True,
        json_response=True,
        host=settings.host,
    )
    uvicorn.run(
        ServiceGate(app, settings),
        host=settings.host,
        port=settings.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
