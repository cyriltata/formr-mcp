import os

import httpx
import pytest
from starlette.testclient import TestClient

from formr_mcp.config import load_local_env, load_settings
from formr_mcp.http import set_transport
from formr_mcp.main import build_app


@pytest.fixture(autouse=True)
def _clear_transport():
    yield
    set_transport(None)


def test_local_env_fills_missing_keys_and_keeps_existing_ones(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("FORMR_MCP_PORT=3999\nFORMR_MCP_HOST=10.0.0.1\n# comment\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("FORMR_MCP_HOST", "127.0.0.1")
    monkeypatch.delenv("FORMR_MCP_PORT", raising=False)
    load_local_env()
    assert os.environ["FORMR_MCP_PORT"] == "3999"
    assert os.environ["FORMR_MCP_HOST"] == "127.0.0.1"


def test_mcp_requires_the_service_secret_and_the_formr_bearer():
    app = build_app(_settings())
    with TestClient(app, base_url="http://127.0.0.1:3001") as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/.well-known/oauth-authorization-server").status_code == 401
        assert client.post("/mcp", json=_whoami()).status_code == 401
        missing_bearer = client.post(
            "/mcp",
            headers={
                "X-Formr-Mcp-Service": "test-service-token",
                "X-Formr-Instance-Url": "http://formr.test",
            },
            json=_whoami(),
        )
        assert missing_bearer.status_code == 401


def test_tool_call_forwards_the_same_authorization_header(tmp_path):
    formr = _Formr()
    set_transport(httpx.MockTransport(formr.handle))
    app = build_app(_settings())
    headers = {
        "X-Formr-Mcp-Service": "test-service-token",
        "X-Formr-Instance-Url": "https://formr.example.com/api/v1",
        "Authorization": "Bearer  formr-user-token",
    }
    with TestClient(app, base_url="http://127.0.0.1:3001") as client:
        response = client.post("/mcp", headers=headers, json=_whoami())
    assert response.status_code == 200
    assert "owner@example.com" in response.text
    assert formr.calls == [("GET", "https://formr.example.com/api/v1/user/me", "Bearer  formr-user-token")]


class _Formr:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.calls.append((request.method, str(request.url), request.headers["authorization"]))
        if request.url.path == "/api/v1/user/me":
            return httpx.Response(200, json={"email": "owner@example.com"})
        return httpx.Response(404, json={"error": "unexpected"})


def _settings():
    return load_settings({"FORMR_MCP_SERVICE_TOKEN": "test-service-token", "FORMR_MCP_HOST": "127.0.0.1"})


def _whoami() -> dict:
    return {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "whoami", "arguments": {}}}
