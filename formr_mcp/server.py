from mcp.server.mcpserver import MCPServer

from formr_mcp import __version__
from formr_mcp.tools import register_all


def build_server() -> MCPServer:
    server = MCPServer(
        name="formr",
        title="formr",
        version=__version__,
        instructions=(
            "Tools call the formr v1 API as the user whose access token is on this request. "
            "import_run_structure replaces a run and expires live sessions. "
            "delete_run, delete_survey, delete_run_file, and session_action change live study data. "
            "There is no API to delete a participant session."
        ),
    )
    register_all(server)
    return server
