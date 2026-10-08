from mcp.server.mcpserver import MCPServer

from formr_mcp.tools import files, results, runs, sessions, surveys, user


def register_all(server: MCPServer) -> None:
    user.register(server)
    runs.register(server)
    sessions.register(server)
    results.register(server)
    files.register(server)
    surveys.register(server)
