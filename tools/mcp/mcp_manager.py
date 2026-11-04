from config.config import Config

from tools.mcp.client import MCPClient


class MCPManager:
    def __init__(self, config: Config):
        self.config = config
        self.client:  dict[str, MCPClient] = {}
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return 

        mcp_configs = self.config.mcp_serves

        if not mcp_configs:
            return 

        for name, server_config in mcp_configs.items():
            if not server_config.enabled:
                continue 

            self._client[name] = MCPClient(
                name = name,
                config = server_config,
                cwd = self.config.cwd,
            )

        connection_tasks = [
            asyncio.wait_for(
                client.connect(),
                timeout=client.config.startup_timeout_sec,
                                   )
            for name, client in self._clients.items()
        ]

        await asyncio.gather(*connection_tasks, return_exception=True)

        self._initialized = True

    def register_tools(self, registry: ToolRegistry) -> int:
        count = 0 

        for client in self._client.values():
            if client.status != MCPServeStatus.CONNECTED:
                continue 

            for tool_info in client.tools:
                mcp_tool = MCPTool(
                    tool_inf = tool_info,
                    client=client,
                    config = self.config,
                    name=f"{client.name}__{tool_info.name}"
                )
                registry.register_mcp_tool(mcp_tool)
                count += 1

        return count

    async def shutdown(self) -> None:
        disconnection_tasks = [client.disconnect() for client in self._clients.values()]

        await asyncio.gather(*disconnection_tasks, return_exceptions = True)
        self._client.clear()
        self._initialized = False



            

    

        
         

        
        

          

