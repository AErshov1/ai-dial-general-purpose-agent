from typing import Optional, Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import CallToolResult, TextContent, ReadResourceResult, TextResourceContents, BlobResourceContents
from pydantic import AnyUrl

from task.tools.mcp.mcp_tool_model import MCPToolModel


class MCPClient:
    """Handles MCP server connection and tool execution"""

    def __init__(self, mcp_server_url: str) -> None:
        self.server_url = mcp_server_url
        self.session: Optional[ClientSession] = None
        self._streams_context = None
        self._session_context = None

    async def connect(self):
        """Connect to MCP server"""
        # 1. Check if session is present, if yes just return to finsh execution
        # 2. Call `streamablehttp_client` method with `server_url` and set as `self._streams_context`
        # 3. Enter `self._streams_context`, result set as `read_stream, write_stream, _`
        # 4. Create ClientSession with streams from above and set as `self._session_context`
        # 5. Enter `self._session_context` and set as self.session
        # 6. Initialize session and print its result to console
        if self.session:
            return

        print(f"Connecting to MCP server at {self.server_url}...")
        self._streams_context = streamablehttp_client(self.server_url)
        read_stream, write_stream, _ = await self._streams_context.__aenter__()
        try:
            self._session_context = ClientSession(read_stream, write_stream)
            self.session = await self._session_context.__aenter__()
            await self.session.initialize()
        except Exception as e:
            await self.close(None, None, None)
            raise e

    async def get_tools(self) -> list[MCPToolModel]:
        """Get available tools from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")

        tools = await self.session.list_tools()
        return [
            MCPToolModel(
                name=tool.name,
                description=tool.description,
                parameters=tool.inputSchema,
            )
            for tool in tools.tools
        ]

    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        """Call a tool on the MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")

        tool_result: CallToolResult = await self.session.call_tool(tool_name, tool_args)
        if not tool_result.content:
            return None

        content = tool_result.content[0]
        if not isinstance(content, TextContent):
            raise NotImplementedError(
                "Currently only TextContent is supported as tool result content.")

        return content.text

    async def get_resource(self, uri: AnyUrl) -> str | bytes:
        """Get specific resource content"""
        raise NotImplementedError()

    async def close(self, exc_type, exc_val, exc_tb):
        """Close connection to MCP server"""
        # 1. Close `self._session_context`
        # 2. Close `self._streams_context`
        # 3. Set session, _session_context and _streams_context as None
        print(f"Closing connection to MCP server at {self.server_url}...")
        if self._session_context:
            self._session_context.__aexit__(exc_type, exc_val, exc_tb)
            self._session_context = None
        if self._streams_context:
            self._streams_context.__aexit__(exc_type, exc_val, exc_tb)
            self._streams_context = None

        self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close(exc_type, exc_val, exc_tb)
        return False
