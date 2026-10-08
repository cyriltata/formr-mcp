# Credentials

formr's public API uses a per-user OAuth client. `client_secret` is shown once, then stored only as a hash (`OAuthHelper::createClient`). That pair is the right credential when a person connects their own external program (a script, Claude Desktop, Cursor) and pastes the secret into that program's secret store.

The admin assistant is a different caller. The user is already logged in. The MCP client runs inside the admin, so it can mint a token for that session instead of collecting a secret.

## What this server is configured with

| Variable | Purpose |
| --- | --- |
| `FORMR_ALLOWED_INSTANCE_URLS` | Optional comma-separated origins. Unset accepts any http(s) instance URL sent on the request |
| `FORMR_MCP_SERVICE_TOKEN` | Shared secret. formr admin sends it as `X-Formr-Mcp-Service` |
| `FORMR_MCP_HOST` | Default `127.0.0.1`. The container forces `0.0.0.0` |
| `FORMR_MCP_PORT` | Default `3001` |
| `FORMR_MCP_ALLOWED_HOSTS` | Host headers accepted when the bind address is not loopback. Default `127.0.0.1:*`, `localhost:*`, `[::1]:*`, `formr-mcp:*` |

`FORMR_MCP_SERVICE_TOKEN` is one value for the deployment, generated once, stored in the formr admin settings and in this server's environment. It identifies the admin process. It is not a formr user.

The server itself exposes every v1 route. The scopes on the minted token are what limit a given chat turn. A diary-authoring turn should use `user:read survey:read survey:write run:read run:write`, so results, sessions, and files stay closed.

## What arrives on each request

`X-Formr-Instance-Url` is the origin of the formr that minted the token, for example `https://study.example.com`. One MCP process can serve many formr instances because the API call goes to that origin. A path other than the origin (or an origin ending in `/api/v1`, which is stripped) is rejected. When `FORMR_ALLOWED_INSTANCE_URLS` is set, an origin outside that list is rejected with 403.

`Authorization: Bearer <access_token>`, minted in PHP at the start of the prompt:

```php
OAuthHelper::getInstance()->createAccessTokenForUser(
    $user,
    'user:read survey:read survey:write run:read run:write',
    false,   // no refresh token
    600      // 10 minutes
);
```

That method already exists. It uses the reserved internal OAuth client and stamps the scope on the token. The user's own API credentials, their labels, and their run allowlists stay untouched. An empty run allowlist means the token can create new runs; a run-restricted client cannot, because a diary run does not exist yet.

When the model loop finishes, or the TTL passes, the admin deletes the token with `OAuthHelper::deleteAccessToken`.

The browser posts the prompt to PHP. PHP holds the bearer token and talks to this server. The token is not placed in HTML, JavaScript, or the MCP server's environment.

## Who may use the prompt box

`createAccessTokenForUser` requires `User::canAccessApi()`, which is admin level 2 or higher. Study authors at level 1 can use the admin UI and cannot call the API. Keep that gate. The prompt box is available to level 2 and above, the same people who can already create an API client. Do not add a second path that bypasses the API's owner checks.

`GET /api/v1/user/me` returns `scopes` and `allowed_runs` for this token. formr rejects a tool call whose scope is missing, and the tool result comes back with status 403.

Every tool call sends formr the same `Authorization` header the admin sent on the MCP request. This server does not mint a second token and does not store the bearer.
