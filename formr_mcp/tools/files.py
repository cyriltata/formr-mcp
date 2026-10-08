from mcp.server.mcpserver import Context, MCPServer

from formr_mcp.client import decode_upload, path_segment
from formr_mcp.models import ApiResult, FileUpload
from formr_mcp.tools.common import call, hints


async def list_files(ctx: Context, name: str) -> ApiResult:
    """List files uploaded to a run. Scope: file:read."""
    return await call(ctx, "GET", f"/runs/{path_segment(name)}/files")


async def upload_run_file(ctx: Context, name: str, file: FileUpload) -> ApiResult:
    """Upload one file to a run. content_base64 is the file bytes. Scope: file:write."""
    try:
        filename, raw = decode_upload(file.filename, file.content_base64)
    except ValueError as exc:
        return ApiResult(ok=False, status=400, error=str(exc))
    return await call(
        ctx,
        "POST",
        f"/runs/{path_segment(name)}/files",
        files={"file": (filename, raw, "application/octet-stream")},
    )


async def delete_run_file(ctx: Context, name: str, filename: str) -> ApiResult:
    """Delete one uploaded run file by its original name. Scope: file:write."""
    return await call(ctx, "DELETE", f"/runs/{path_segment(name)}/files/{path_segment(filename)}")


def register(server: MCPServer) -> None:
    server.tool(annotations=hints("List run files", read_only=True))(list_files)
    server.tool(annotations=hints("Upload run file", destructive=False))(upload_run_file)
    server.tool(annotations=hints("Delete run file", destructive=True, idempotent=True))(delete_run_file)
