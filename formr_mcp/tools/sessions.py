from mcp.server.mcpserver import Context, MCPServer

from formr_mcp.client import path_segment, payload
from formr_mcp.models import ApiResult, SessionAction, SessionCreate
from formr_mcp.tools.common import call, csv, flag, hints


async def list_sessions(
    ctx: Context,
    name: str,
    limit: int | None = None,
    offset: int | None = None,
    active: bool | None = None,
    testing: bool | None = None,
) -> ApiResult:
    """List participant sessions in a run. Scope: session:read."""
    return await call(
        ctx,
        "GET",
        f"/runs/{path_segment(name)}/sessions",
        params={"limit": limit, "offset": offset, "active": flag(active), "testing": flag(testing)},
    )


async def get_session(ctx: Context, name: str, session: str) -> ApiResult:
    """Return one participant session. Scope: session:read."""
    return await call(ctx, "GET", f"/runs/{path_segment(name)}/sessions/{path_segment(session)}")


async def create_session(ctx: Context, name: str, session: SessionCreate | None = None) -> ApiResult:
    """Create one random session, or sessions for the given codes. Scope: session:write.

    The v1 API has no DELETE for sessions. Ending or moving a session is session_action.
    """
    body = payload(session) if session is not None else {}
    return await call(ctx, "POST", f"/runs/{path_segment(name)}/sessions", json_body=body)


async def session_action(ctx: Context, name: str, session: str, action: SessionAction) -> ApiResult:
    """Run end_external, toggle_testing, move_to_position, execute, or advance. Scope: session:write."""
    return await call(
        ctx,
        "POST",
        f"/runs/{path_segment(name)}/sessions/{path_segment(session)}/actions",
        json_body=payload(action),
    )


async def list_unit_sessions(
    ctx: Context,
    name: str,
    limit: int | None = None,
    offset: int | None = None,
    session: list[str] | None = None,
    testing: bool | None = None,
    since: str | None = None,
) -> ApiResult:
    """List per-unit session history for a run. Scope: session:read."""
    return await call(
        ctx,
        "GET",
        f"/runs/{path_segment(name)}/unit_sessions",
        params={
            "limit": limit,
            "offset": offset,
            "session": csv(session),
            "testing": flag(testing),
            "since": since,
        },
    )


def register(server: MCPServer) -> None:
    server.tool(annotations=hints("List sessions", read_only=True))(list_sessions)
    server.tool(annotations=hints("Get session", read_only=True))(get_session)
    server.tool(annotations=hints("Create session", destructive=False))(create_session)
    server.tool(annotations=hints("Session action", destructive=True))(session_action)
    server.tool(annotations=hints("List unit sessions", read_only=True))(list_unit_sessions)
