from mcp.server.mcpserver import Context, MCPServer

from formr_mcp.client import decode_upload, path_segment, payload
from formr_mcp.models import ApiResult, SurveyUpdate, SurveyUpload
from formr_mcp.tools.common import call, hints


async def list_surveys(ctx: Context, name: str | None = None) -> ApiResult:
    """List surveys owned by this user. Scope: survey:read."""
    return await call(ctx, "GET", "/surveys", params={"name": name})


async def get_survey(ctx: Context, name: str) -> ApiResult:
    """Return one survey's item table as JSON. Scope: survey:read."""
    return await call(ctx, "GET", f"/surveys/{path_segment(name)}", params={"format": "json"})


async def create_survey(ctx: Context, survey: SurveyUpload) -> ApiResult:
    """Create a survey from a spreadsheet upload or a Google Sheet URL. Scope: survey:write.

    The v1 API does not accept an item-table JSON body. Send filename plus content_base64,
    or google_sheet.
    """
    if survey.google_sheet:
        return await call(ctx, "POST", "/surveys", form={"google_sheet": survey.google_sheet})
    try:
        filename, raw = decode_upload(survey.filename or "", survey.content_base64 or "")
    except ValueError as exc:
        return ApiResult(ok=False, status=400, error=str(exc))
    return await call(
        ctx,
        "POST",
        "/surveys",
        files={"file": (filename, raw, "application/octet-stream")},
    )


async def update_survey(ctx: Context, name: str, settings: SurveyUpdate) -> ApiResult:
    """Patch survey settings, or pass google_sheet to sync items. Scope: survey:write."""
    body = payload(settings)
    if not body:
        return ApiResult(ok=False, status=400, error="No survey settings to update")
    return await call(ctx, "PATCH", f"/surveys/{path_segment(name)}", json_body=body)


async def delete_survey(ctx: Context, name: str) -> ApiResult:
    """Delete a survey owned by this user. Scope: survey:write."""
    return await call(ctx, "DELETE", f"/surveys/{path_segment(name)}")


def register(server: MCPServer) -> None:
    server.tool(annotations=hints("List surveys", read_only=True))(list_surveys)
    server.tool(annotations=hints("Get survey", read_only=True))(get_survey)
    server.tool(annotations=hints("Create survey", destructive=False))(create_survey)
    server.tool(annotations=hints("Update survey", destructive=False))(update_survey)
    server.tool(annotations=hints("Delete survey", destructive=True, idempotent=True))(delete_survey)
