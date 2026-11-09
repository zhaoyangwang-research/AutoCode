from tools.base import Tool, ToolInvocation, ToolResult
import logging 
from pathlib import Path
from typing import Any
from tools.builtin import ReadFileTool, get_all_builtin_tools



logger = logging.getLogger(__name__)

class ToolRegistry:
    def __init__(self, config: Config):
        self._tools: dict[str, Tool] = {}
        self._mcp_tools: dict[str, Tool] = {}

        self.config = config

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            logger.warning(f"Overwriting exisiting tool: {tool.name}")

        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def register_mcp_tool(self, name: str, tool: Tool) -> None:
     
        self._mcp_tools[tool.name] = tool
        logger.debug(f"Registered MCP tool: {tool.name}")


    def unregister(self, name: str) -> bool:
        if name in self._tools:
            del self._tools[name]
            return True
        return False


    def get(self, name: str) -> Tool | None:
        if name in self._tools:
            return self._tools[name]

        elif name in self._mcp_tools:
            return self._mcp_tools[name]

        return None

    def get_tools(self) -> list[Tool]:
        tools: list[Tool] = []

        for tool in self._tools.values():
            tools.append(tool)

        for mcp_tool in self._mcp_tools.values():
            tools.append(tool)

        if self.config.allowed_tools:
            allowed_set = set(self.config.allowed_tools)
            tools = [t for t in tools if t.name in allowed_set]

        return tools

    def get_schemas(self) -> list[dict[str, Any]]:
        return [tool.to_openai_schema() for tool in self.get_tools()]

    async def invoke(
            self, 
            name: str, 
            params: dict[str, Any], 
            cwd: Path | None,
            approval_manger: ApprovalManager | None = None,
    ) -> ToolResult:
        tool = self.get(name)
        if tool is None:
            return ToolResult.error_result(
                f"Unknown tool: {name}",
                metadata = {"tool_name": name},
            )

        validation_errors = tool.validate_params(params)
        if validation_errors:
            return ToolResult.error_result(
                f"Invalid parameters: {';'.join(validation_errors)}",
                metadata = {
                    "tool_name": name, 
                    "validation_errors": validation_errors,
                },
            )

        invocation = ToolInvocation(
            params = params,
            cwd = cwd,
        )

# check for different tools for built-in tools and give confirmation in tools.  
        if approval_manger:
            confirmation = await tool.get_confirmation()
            if confirmation:
                context = approval_manger(
                    tool_name = name,
                    params = params,
                    is_mutating=tool.is_mutating(params),
                    affected_paths= confirmation.affected_paths,
                    command=confirmation.command,
                    is_dangerous=confirmation.is_dangerous,
                )
                
                decision = await approval_manager.check_approval(context)

        try:
            result = await tool.execute(invocation)

        except Exception as e:
            logger.exception(f"Tool {name} raised unexpeceted error")
            result= ToolResult.error_result(
                f"Internal error {str(e)}",
                metadata ={
                    "tool_name",
                    name,
                },
            )
        return result 

def create_default_registry(config: Config) -> ToolRegistry:
    registry = ToolRegistry(config)

    for tool_class in get_all_builtin_tools():
        registry.register(tool_class(config))

    for subagent_def in get_default_subagent_definition():
        registry.register(SubagentTool(config,subagent_def ))

    return registry








        
        

         


    

    

    

    

    

    