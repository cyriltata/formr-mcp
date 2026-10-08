from typing import Any

import httpx

_transport: httpx.AsyncBaseTransport | None = None


def set_transport(transport: httpx.AsyncBaseTransport | None) -> None:
    """Replace the outbound HTTP transport. Tests use this; production leaves it unset."""
    global _transport
    _transport = transport


def async_client(**kwargs: Any) -> httpx.AsyncClient:
    if _transport is not None:
        kwargs["transport"] = _transport
    return httpx.AsyncClient(**kwargs)
