from typing import Any

from mcp.server.mcpserver import Context
from mcp_types import ToolAnnotations

from formr_mcp.client import FormrClient
from formr_mcp.config import InstanceNotAllowed
from formr_mcp.models import ApiResult


def hints(title: str, *, read_only: bool = False, destructive: bool = False, idempotent: bool = False) -> ToolAnnotations:
    return ToolAnnotations(
        title=title,
        read_only_hint=read_only,
        destructive_hint=destructive,
        idempotent_hint=idempotent,
        open_world_hint=True,
    )


async def call(ctx: Context, method: str, path: str, **kwargs: Any) -> ApiResult:
    try:
        client = FormrClient.from_context(ctx)
    except InstanceNotAllowed as exc:
        return ApiResult(ok=False, status=403, error=str(exc))
    except PermissionError as exc:
        return ApiResult(ok=False, status=401, error=str(exc))
    except ValueError as exc:
        return ApiResult(ok=False, status=400, error=str(exc))
    return await client.request(method, path, **kwargs)


def csv(values: list[str] | None) -> str | None:
    if not values:
        return None
    return ",".join(values)


def flag(value: bool | None) -> str | None:
    if value is None:
        return None
    return "true" if value else "false"
