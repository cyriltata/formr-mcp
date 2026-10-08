import base64
import logging
from collections.abc import Mapping
from typing import Any
from urllib.parse import quote

import httpx
from mcp.server.mcpserver import Context

from formr_mcp.admin_context import admin_instance, inbound_authorization
from formr_mcp.config import INSTANCE_HEADER, INSTANCE_HEADER_NAME, Settings
from formr_mcp.http import async_client
from formr_mcp.models import ApiResult

logger = logging.getLogger("formr_mcp")

_settings: Settings | None = None
MAX_UPLOAD_BYTES = 12 * 1024 * 1024


def configure(settings: Settings) -> None:
    global _settings
    _settings = settings


def settings() -> Settings:
    if _settings is None:
        raise RuntimeError("formr MCP settings are not loaded")
    return _settings


class FormrClient:
    def __init__(self, origin: str, authorization: str) -> None:
        self.origin = origin
        self.authorization = authorization

    @classmethod
    async def from_context(cls, ctx: Context) -> "FormrClient":
        authorization = inbound_authorization.get() or _header(ctx.headers, "authorization")
        if not authorization.lower().startswith("bearer ") or not authorization[7:].strip():
            raise PermissionError("Authorization: Bearer <formr access token> is required")
        origin = admin_instance.get()
        if not origin:
            raw = _header(ctx.headers, INSTANCE_HEADER)
            if not raw:
                raise ValueError(f"{INSTANCE_HEADER_NAME} is required")
            origin = settings().resolve_instance(raw)
        return cls(origin, authorization)

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        form: Mapping[str, str] | None = None,
        files: Mapping[str, tuple[str, bytes, str]] | None = None,
    ) -> ApiResult:
        url = f"{self.origin}/api/v1{path}"
        query = {key: value for key, value in (params or {}).items() if value is not None}
        headers = {"Authorization": self.authorization, "Accept": "application/json"}
        try:
            async with async_client(timeout=httpx.Timeout(120.0), follow_redirects=False, trust_env=False) as http:
                response = await http.request(
                    method,
                    url,
                    params=query or None,
                    json=json_body,
                    data=form,
                    files=files,
                    headers=headers,
                )
        except httpx.HTTPError as exc:
            logger.info("formr %s %s %s failed: %s", self.origin, method, path, type(exc).__name__)
            return ApiResult(ok=False, status=0, error=str(exc))
        return _result(self.origin, method, path, response)


def path_segment(value: str) -> str:
    return quote(value, safe="")


def decode_upload(filename: str, content_base64: str) -> tuple[str, bytes]:
    name = filename.replace("\\", "/").rsplit("/", 1)[-1].strip()
    if not name or name in {".", ".."} or "/" in name:
        raise ValueError("Invalid file name")
    try:
        raw = base64.b64decode(content_base64, validate=True)
    except Exception as exc:
        raise ValueError("content_base64 is not valid base64") from exc
    if not raw:
        raise ValueError("file is empty")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise ValueError("file exceeds 12MB")
    return name, raw


def _header(headers: Mapping[str, str] | None, name: str) -> str:
    if not headers:
        return ""
    wanted = name.lower()
    for key, value in headers.items():
        if str(key).lower() == wanted:
            return str(value)
    return ""


def _result(origin: str, method: str, path: str, response: httpx.Response) -> ApiResult:
    logger.info("formr %s %s %s -> %s", origin, method, path, response.status_code)
    body: Any = None
    if response.content:
        content_type = response.headers.get("content-type", "")
        if "json" in content_type or response.content[:1] in (b"{", b"["):
            body = response.json()
        else:
            body = {"message": "formr returned a non-JSON body", "content_type": content_type}
    if response.status_code >= 400:
        message = response.reason_phrase
        if isinstance(body, dict):
            message = str(body.get("message") or message)
        return ApiResult(ok=False, status=response.status_code, body=body, error=message)
    return ApiResult(ok=True, status=response.status_code, body=body)


def payload(model: Any) -> dict[str, Any]:
    data = model.model_dump(exclude_unset=True)
    return {key: value for key, value in data.items() if value is not None}
