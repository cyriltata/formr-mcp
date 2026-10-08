#!/bin/sh
set -eu

# 127.0.0.1 inside the container is not the host and is not reachable from
# other containers. .env may set FORMR_MCP_HOST for a local process; ignore it here.
export FORMR_MCP_HOST=0.0.0.0

exec formr-mcp
