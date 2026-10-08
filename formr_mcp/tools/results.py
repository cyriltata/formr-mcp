from mcp.server.mcpserver import Context, MCPServer

from formr_mcp.client import path_segment
from formr_mcp.models import ApiResult
from formr_mcp.tools.common import call, csv, hints


async def get_results(
    ctx: Context,
    name: str,
    sessions: list[str] | None = None,
    surveys: list[str] | None = None,
    items: list[str] | None = None,
) -> ApiResult:
    """Download survey results for a run. Scope: data:read."""
    return await call(
        ctx,
        "GET",
        f"/runs/{path_segment(name)}/results",
        params={"sessions": csv(sessions), "surveys": csv(surveys), "items": csv(items)},
    )


def register(server: MCPServer) -> None:
    server.tool(annotations=hints("Get results", read_only=True))(get_results)
