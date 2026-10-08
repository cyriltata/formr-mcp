import hashlib
import hmac

from starlette.responses import JSONResponse

from formr_mcp.admin_context import admin_instance, inbound_authorization
from formr_mcp.config import INSTANCE_HEADER, InstanceNotAllowed, Settings


def same_secret(left: str, right: str) -> bool:
    return hmac.compare_digest(
        hashlib.sha256(left.encode()).digest(),
        hashlib.sha256(right.encode()).digest(),
    )


class ServiceGate:
    """Admit only a formr admin request that carries the deployment secret."""

    def __init__(self, app: object, settings: Settings) -> None:
        self.app = app
        self.settings = settings

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = scope.get("path", "")
        if path == "/health":
            await JSONResponse({"status": "ok"})(scope, receive, send)
            return
        provided = _header(scope.get("headers", []), "x-formr-mcp-service")
        if not provided or not same_secret(provided, self.settings.service_token):
            await _error(scope, receive, send, 401, "MCP service token rejected")
            return
        if path != "/mcp":
            await self.app(scope, receive, send)
            return
        await self._admin(scope, receive, send)

    async def _admin(self, scope, receive, send) -> None:
        authorization = _header(scope.get("headers", []), "authorization")
        if not _bearer(authorization):
            await _error(scope, receive, send, 401, "Authorization: Bearer <formr access token> is required")
            return
        instance = _header(scope.get("headers", []), INSTANCE_HEADER)
        try:
            origin = self.settings.resolve_instance(instance)
        except ValueError as exc:
            await _error(scope, receive, send, 400, str(exc))
            return
        except InstanceNotAllowed as exc:
            await _error(scope, receive, send, 403, str(exc))
            return
        instance_token = admin_instance.set(origin)
        auth_token = inbound_authorization.set(authorization)
        try:
            await self.app(scope, receive, send)
        finally:
            inbound_authorization.reset(auth_token)
            admin_instance.reset(instance_token)


async def _error(scope, receive, send, status: int, message: str) -> None:
    await JSONResponse({"error": message}, status_code=status)(scope, receive, send)


def _bearer(value: str) -> str:
    prefix = "bearer "
    if value.lower().startswith(prefix) and value[len(prefix) :].strip():
        return value
    return ""


def _header(pairs: list[tuple[bytes, bytes]], name: str) -> str:
    wanted = name.lower().encode()
    for key, value in pairs:
        if key.lower() == wanted:
            return value.decode("latin1")
    return ""
