import contextvars

# Set for one admin MCP request. Tool calls read these instead of a stored credential.
admin_instance: contextvars.ContextVar[str | None] = contextvars.ContextVar("formr_admin_instance", default=None)
inbound_authorization: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "formr_inbound_authorization", default=None
)
