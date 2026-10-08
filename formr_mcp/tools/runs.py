from typing import Any

from mcp.server.mcpserver import Context, MCPServer

from formr_mcp.client import path_segment, payload
from formr_mcp.models import ApiResult, RunUpdate
from formr_mcp.tools.common import call, hints


async def list_runs(ctx: Context, name: str | None = None, public: int | None = None) -> ApiResult:
    """List runs owned by this user. Scope: run:read."""
    return await call(ctx, "GET", "/runs", params={"name": name, "public": public})


async def get_run(ctx: Context, name: str) -> ApiResult:
    """Return one run's settings. Scope: run:read."""
    return await call(ctx, "GET", f"/runs/{path_segment(name)}")


async def create_run(ctx: Context, name: str) -> ApiResult:
    """Create an empty run. Name starts with a letter and uses letters, digits, and hyphens. Scope: run:write."""
    return await call(ctx, "POST", f"/runs/{path_segment(name)}")


async def update_run(ctx: Context, name: str, settings: RunUpdate) -> ApiResult:
    """Patch run settings. Cannot rename the run. Scope: run:write."""
    body = payload(settings)
    if not body:
        return ApiResult(ok=False, status=400, error="No run settings to update")
    return await call(ctx, "PATCH", f"/runs/{path_segment(name)}", json_body=body)


async def delete_run(ctx: Context, name: str) -> ApiResult:
    """Delete a run and its units. Scope: run:write."""
    return await call(ctx, "DELETE", f"/runs/{path_segment(name)}")


async def get_run_structure(ctx: Context, name: str) -> ApiResult:
    """Export the run's units, including item tables the owner owns. Scope: run:read."""
    return await call(ctx, "GET", f"/runs/{path_segment(name)}/structure")


async def import_run_structure(ctx: Context, name: str, structure: dict[str, Any]) -> ApiResult:
    """Replace every unit in the run. Live participant sessions on that run are expired. Scope: run:write."""
    return await call(ctx, "PUT", f"/runs/{path_segment(name)}/structure", json_body=structure)


def register(server: MCPServer) -> None:
    server.tool(annotations=hints("List runs", read_only=True))(list_runs)
    server.tool(annotations=hints("Get run", read_only=True))(get_run)
    server.tool(annotations=hints("Create run", destructive=False))(create_run)
    server.tool(annotations=hints("Update run settings", destructive=False))(update_run)
    server.tool(annotations=hints("Delete run", destructive=True, idempotent=True))(delete_run)
    server.tool(annotations=hints("Get run structure", read_only=True))(get_run_structure)
    server.tool(annotations=hints("Replace run structure", destructive=True, idempotent=True))(import_run_structure)
