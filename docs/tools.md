# Tools

Each tool is one call to `/api/v1`. The formr API enforces the scope. A token without it comes back as `ok: false` and status 403.

| Tool | API | Scope |
| --- | --- | --- |
| `whoami` | `GET /user/me` | `user:read` |
| `update_user` | `PATCH /user/me` | `user:write` |
| `list_runs` | `GET /runs` | `run:read` |
| `get_run` | `GET /runs/{name}` | `run:read` |
| `create_run` | `POST /runs/{name}` | `run:write` |
| `update_run` | `PATCH /runs/{name}` | `run:write` |
| `delete_run` | `DELETE /runs/{name}` | `run:write` |
| `get_run_structure` | `GET /runs/{name}/structure` | `run:read` |
| `import_run_structure` | `PUT /runs/{name}/structure` | `run:write` |
| `list_sessions` | `GET /runs/{name}/sessions` | `session:read` |
| `get_session` | `GET /runs/{name}/sessions/{session}` | `session:read` |
| `create_session` | `POST /runs/{name}/sessions` | `session:write` |
| `session_action` | `POST /runs/{name}/sessions/{session}/actions` | `session:write` |
| `list_unit_sessions` | `GET /runs/{name}/unit_sessions` | `session:read` |
| `get_results` | `GET /runs/{name}/results` | `data:read` |
| `list_files` | `GET /runs/{name}/files` | `file:read` |
| `upload_run_file` | `POST /runs/{name}/files` | `file:write` |
| `delete_run_file` | `DELETE /runs/{name}/files/{filename}` | `file:write` |
| `list_surveys` | `GET /surveys` | `survey:read` |
| `get_survey` | `GET /surveys/{name}` | `survey:read` |
| `create_survey` | `POST /surveys` | `survey:write` |
| `update_survey` | `PATCH /surveys/{name}` | `survey:write` |
| `delete_survey` | `DELETE /surveys/{name}` | `survey:write` |

`import_run_structure` replaces every unit and expires live participant sessions on that run.

## Routes that are not separate tools

- `DELETE /v1/runs/{name}/sessions` does not exist. The write operations are `create_session` and `session_action` (`end_external`, `toggle_testing`, `move_to_position`, `execute`, `advance`).
- `GET /v1/runs/{name}/sessions/{session}` and `POST .../actions` are real routes, so they have tools.
- `PATCH /v1/user/me` is a real route (`user:write`), so `update_user` exists.
- OAuth (`/api/oauth/access_token`) and the legacy v0 API are not tools. The admin mints the bearer token and this server forwards that same header to formr.
- `POST /surveys` accepts a spreadsheet file or a Google Sheet URL. It does not accept an item-table JSON body. `create_survey` follows that.
