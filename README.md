# formr MCP server

Standalone Python service. The formr admin chat UI talks to it over HTTP. This process calls the formr v1 API with the access token the admin mints for the logged-in user.

Requires Python 3.12 or newer. The system `python3` on this host is 3.9 and cannot install the MCP SDK.

## Run on localhost

The package is installed editable, so Python reads `formr_mcp/` from this directory. `formr-mcp-dev` loads `.env` itself and restarts when a file in that directory changes. Docker is not involved.

```bash
cd /var/www/formr-mcp
/usr/local/bin/python3.12 -m venv .venv          # once
.venv/bin/pip install -e ".[dev]"                # once, and again only when dependencies change
.venv/bin/formr-mcp-dev
```

The server listens on `FORMR_MCP_HOST`:`FORMR_MCP_PORT` (default `127.0.0.1:3001`). Stop the `formr-mcp` container first if it is already published on that port.

`formr-mcp` is the same server without the file watcher. The container uses that command.

## Docker

The image listens on `0.0.0.0` inside the container. Compose publishes that port on the host loopback only, and injects `.env` at runtime. The file is not copied into the image.

```bash
cd /var/www/formr-mcp
cp .env.example .env   # then set FORMR_MCP_SERVICE_TOKEN
docker compose up --build -d
curl -s http://127.0.0.1:3001/health
```

formr admin on this host calls `http://127.0.0.1:3001/mcp`. Another container on the same Compose network calls `http://formr-mcp:3001/mcp`. Change `FORMR_MCP_PORT` in `.env` if 3001 is taken; both the process and the published port follow it.

The container is the production process: auto-reload is off, the published port stays on the host loopback, and Host-header checks stay on for `127.0.0.1`, `localhost`, `[::1]`, and `formr-mcp`. Add any other caller hostname to `FORMR_MCP_ALLOWED_HOSTS`. Set `FORMR_ALLOWED_INSTANCE_URLS` to the formr origins that may call; without it the process accepts any http(s) instance URL.

- `GET /health` returns `{"status":"ok"}` with no credentials.
- `POST /mcp` is the MCP Streamable HTTP endpoint. Every request needs three headers: `X-Formr-Mcp-Service` (the deployment secret), `X-Formr-Instance-Url` (the calling formr origin, for example `https://formr.example.com`), and `Authorization: Bearer` (that user's short-lived formr token).

The server calls `{X-Formr-Instance-Url}/api/v1/...` and sends the same `Authorization: Bearer` value it received. Set `FORMR_ALLOWED_INSTANCE_URLS` to a comma-separated list of origins to restrict which instances may call. Leave it unset to accept any http(s) instance URL.

## Tools

One tool per v1 route. See `docs/tools.md`. There is no session-delete tool: the API does not have that route. `PATCH /v1/user/me` and `GET` plus `POST .../actions` on a single session are included because they exist on the API.
