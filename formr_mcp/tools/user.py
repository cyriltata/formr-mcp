from mcp.server.mcpserver import Context, MCPServer

from formr_mcp.client import payload
from formr_mcp.models import ApiResult, UserUpdate
from formr_mcp.tools.common import call, hints


async def whoami(ctx: Context) -> ApiResult:
    """Return the formr user, token scopes, and run allowlist. Scope: user:read."""
    return await call(ctx, "GET", "/user/me")


async def update_user(ctx: Context, profile: UserUpdate) -> ApiResult:
    """Update first_name, last_name, or affiliation. Scope: user:write."""
    body = payload(profile)
    if not body:
        return ApiResult(ok=False, status=400, error="No profile fields to update")
    return await call(ctx, "PATCH", "/user/me", json_body=body)


def register(server: MCPServer) -> None:
    server.tool(name="whoami", annotations=hints("Who am I", read_only=True))(whoami)
    server.tool(name="update_user", annotations=hints("Update user profile"))(update_user)
