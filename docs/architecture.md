# Architecture

## Roles

Three processes, one user.

```text
browser                formr admin (PHP)              formr-mcp                 formr API
  |                         |                            |                          |
  | prompt                  |                            |                          |
  |------------------------>|                            |                          |
  |                         | mint access token          |                          |
  |                         |----------------------------|------------------------->|
  |                         |         token (minutes)    |                          |
  |                         |<---------------------------|--------------------------|
  |                         | MCP tools/list, tools/call |                          |
  |                         | Authorization: Bearer ...  |                          |
  |                         |--------------------------->|                          |
  |                         |                            | /api/v1/...              |
  |                         |                            |------------------------->|
  |                         | tool result                |                          |
  |                         |<---------------------------|                          |
  | plan, then confirmation |                            |                          |
  |<------------------------|                            |                          |
```

- **Browser.** Shows the prompt box and the plan. It never sees the access token, the service token, or the model key.
- **formr admin.** The MCP client and the model loop. It already has the logged-in user from the admin session. It mints the token, calls this server, and deletes the token when the turn ends.
- **formr-mcp.** Tools only. It translates a tool call into one formr API request. It does not call a language model.
- **formr API.** Existing `/api/v1`, OAuth bearer, owner-scoped. This server does not open the database.

The model key stays in formr admin configuration, next to the other admin secrets.

## Transport

Streamable HTTP, stateless. Each MCP request carries the credentials for that turn. The server creates a fresh MCP session per request and does not remember tokens between requests.

Bind to the docker network (`127.0.0.1` or the compose service name). The public internet reaches formr admin, not this port.

The server is Python 3.12 (`mcp.server.mcpserver.MCPServer`) on stateless Streamable HTTP at `/mcp`. Tool handlers live in `formr_mcp/tools/` and set MCP annotations for read-only and destructive calls. `ServiceGate` accepts `/mcp` only when `X-Formr-Mcp-Service` matches.

## Request pipeline

1. Require `X-Formr-Mcp-Service` to match `FORMR_MCP_SERVICE_TOKEN`.
2. Require `X-Formr-Instance-Url` and `Authorization: Bearer`.
3. The tool sends that same `Authorization` value to `{X-Formr-Instance-Url}/api/v1/...`. This server does not store it and does not mint another token.
4. formr enforces the OAuth scope. A token that is too narrow gets status 403 in the tool result. Handlers do not retry.
5. A non-2xx API response is returned as `ApiResult` (`ok`, `status`, `body`, `error`). Logs record the method, path, and status, not the bearer token.

## Two phases for a prompt

`PUT /api/v1/runs/{name}/structure` replaces every unit and expires live participant sessions. A prompt must not do that on the first model step.

1. **Plan.** Read tools plus `create_run` / `create_survey` on names the user does not already have. The model returns a short plan: run name, survey names, unit order.
2. **Apply.** The admin shows the plan. After the user confirms, the client may call `import_run_structure`. The tool's description tells the model to wait for that confirmation. The admin enforces it by withholding the write until the user accepts. A newly created empty run is the expected target.

## What a diary prompt does

1. `whoami`, `list_runs`, `list_surveys` — avoid taken names.
2. `create_run` with a hyphenated name.
3. `create_survey` for the intake survey and the diary survey. The diary survey needs an expiry so the loop can continue.
4. `update_run` for title and description.
5. After confirmation, `import_run_structure` with Survey, Pause, Survey, SkipBackward, and an end page.

An Email unit needs an `account_id` the run owner already owns. The API has no email-account resource, so the first diary recipe uses a Pause with instructions and leaves the reminder email for the run editor.

## What this server does not do

The admin session and choosing which scopes to mint stay in PHP. The server exposes every v1 route, including results, sessions, and files. A diary-authoring token should still be minted with only `user:read`, `survey:read`, `survey:write`, `run:read`, and `run:write`, so those other tools fail closed with 403. Sharing surveys between users is not an API route.
