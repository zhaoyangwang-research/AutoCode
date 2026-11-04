from enum import Enum
from pathlib import Path
from config.config import MCPServeConfig
from fastmcp import Client
from fastmcp.client.transports import StdioTransport, SSETransport
import os



class MCPServerStatus(str, Enum):
    DISCOUNTED = 'disconnected'
    CONNECTING = 'connecting'
    CONNECTED = 'connected'
    ERROR = 'error'


@dataclass
class MCPToolInfo:
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    server_name:  str = ""





class MCPClient:
    def __init__(
            self,
            name: str,
            config: MCPServeConfig,
            cwd, Path,
    ) -> None:
        self.name = name
        self.config = config 
        self.cwd = cwd
        self.status = MCPServeConfig.DISCONNECTED
        self._client: Client | None = None


        self._tools: dict[str, MCPToolInfo] = dict()

    def _create_transport(self) -> StdioTransport | SSETransport:
        if self.config.command:
            env = os.environ.copy()
            env.update(self.config.env)

            return StdioTransport(
                command = self.config.command,
                args = list(self.config.args),
                env=env,
                cwd=str(self.config.cwd or self.cwd),
            )
        else:
            return SSETransport(url=self.config.url)



    async def connect(self) -> None:
        if self.status == MCPServeConfig.CONNECTED:
            return

        self.status = MCPServerStatus.CONNECTING

        try:
            self._client = Client(transport=self._create_transport())

            await self.)client.__aenter__()
            tool_result = await self._client.list_tools()

            for tool in tool_result:
                self._tools(tool.name) = MCPToolInfo(
                    name = tool.name,
                    desception=tool.description or "",
                    input_schema = (
                        tool.input_schema if hasattr(tool, "inputSchema") else {}
                    ),
                    server_name = self.name,
                )
            self.status = MCPServerStatus.CONNECTED

        except Exception:
            self.status = MCPServerStatus.ERROR
            raise 

    async def disconnect(self) -> None:
        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client= None

        self._tools.clear()
        self.status = MCPServerStatus.DISCONNECTED





    
            

