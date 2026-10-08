import hashlib
import hmac

from starlette.responses import JSONResponse

from formr_mcp.config import INSTANCE_HEADER, InstanceNotAllowed, Settings


def same_secret(left: str, right: str) -> bool:
    return hmac.compare_digest(
        hashlib.sha256(left.encode()).digest(),
        hashlib.sha256(right.encode()).digest(),
    )


class ServiceGate:
    """Require the deployment secret and a formr instance URL on every MCP request."""

    def __init__(self, app: object, settings: Settings) -> None:
        self.app = app
        self.settings = settings

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        if scope.get("path") == "/health":
            await JSONResponse({"status": "ok"})(scope, receive, send)
            return
        provided = _header(scope.get("headers", []), "x-formr-mcp-service")
        if not provided or not same_secret(provided, self.settings.service_token):
            await JSONResponse({"error": "MCP service token rejected"}, status_code=401)(scope, receive, send)
            return
        instance = _header(scope.get("headers", []), INSTANCE_HEADER)
        try:
            self.settings.resolve_instance(instance)
        except ValueError as exc:
            await JSONResponse({"error": str(exc)}, status_code=400)(scope, receive, send)
            return
        except InstanceNotAllowed as exc:
            await JSONResponse({"error": str(exc)}, status_code=403)(scope, receive, send)
            return
        await self.app(scope, receive, send)


def _header(pairs: list[tuple[bytes, bytes]], name: str) -> str:
    wanted = name.lower().encode()
    for key, value in pairs:
        if key.lower() == wanted:
            return value.decode("latin1")
    return ""
