import json
import os
import sys
import asyncio
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

# Set Windows event loop policy if on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from remote_mcp_agent.prompt import NOTION_PROMPT

# ---- MCP Library ----
# https://github.com/modelcontextprotocol/servers
# https://smithery.ai/
# ---- Notion -----
# https://developers.notion.com/docs/mcp
# https://github.com/makenotion/notion-mcp-server
# https://github.com/makenotion/notion-mcp-server/blob/main/scripts/notion-openapi.json

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
if NOTION_API_KEY is None:
    raise ValueError("NOTION_API_KEY is not set")

NOTION_MCP_HEADERS = json.dumps(
    {"Authorization": f"Bearer {NOTION_API_KEY}", "Notion-Version": "2022-06-28"}
)

# Create a function to get the correct command for the platform
def get_mcp_command():
    if sys.platform == 'win32':
        # On Windows, use the full path to npx.cmd
        node_path = os.path.join(os.path.dirname(sys.executable), 'Scripts' if os.path.exists(os.path.join(os.path.dirname(sys.executable), 'Scripts')) else '')
        npx_cmd = os.path.join(node_path, 'npx.cmd')
        return npx_cmd, ["-y", "@notionhq/notion-mcp-server"]
    else:
        return "npx", ["-y", "@notionhq/notion-mcp-server"]

# Get the appropriate command and arguments
mcp_cmd, mcp_args = get_mcp_command()

root_agent = Agent(
    model="gemini-2.0-flash",
    name="Notion_MCP_Agent",
    instruction=NOTION_PROMPT,
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command=mcp_cmd,
                args=mcp_args,
                env={
                    "OPENAPI_MCP_HEADERS": NOTION_MCP_HEADERS,
                    "PATH": os.environ.get("PATH", "")  # Pass through the PATH
                
                },
            )
        ),
    ],
)
