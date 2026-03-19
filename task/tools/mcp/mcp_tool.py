import json
from typing import Any

from aidial_sdk.chat_completion import Message

from task.tools.base import BaseTool
from task.tools.mcp.mcp_client import MCPClient
from task.tools.mcp.mcp_tool_model import MCPToolModel
from task.tools.models import ToolCallParams


class MCPTool(BaseTool):

    def __init__(self, client: MCPClient, mcp_tool_model: MCPToolModel):
        # 1. Set client
        # 2. Set mcp_tool_model
        self.mcp = client
        self.tool_model = mcp_tool_model

    async def _execute(self, tool_call_params: ToolCallParams) -> str | Message:
        # 1. Load arguments wit `json`
        # 2. Get content with mcp client tool call
        # 3. Append retrieved content to stage
        # 4. return content
        arguments = json.loads(tool_call_params.tool_call.function.arguments)
        print(f"{'#'*80}\n TOOL CALL <MCP>: {self.name}\n=> Arguments: {arguments}\n")
        content = await self.mcp.call_tool(self.name, arguments)
        print(f"=> Result: {content}\n{'#'*80}")
        return content

    @property
    def name(self) -> str:
        return self.tool_model.name

    @property
    def description(self) -> str:
        return self.tool_model.description

    @property
    def parameters(self) -> dict[str, Any]:
        return self.tool_model.parameters
