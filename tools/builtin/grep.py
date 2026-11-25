import re
from tools.base import Tool, ToolKind, ToolInvocation, ToolResult
from pydantic import BaseModel, Field

from utils.paths import resolve_path

class GrepParams(BaseModel):
    pattern: str = Field(..., description = 'Regular expression patterns to search for' )
    path: str = Field(".", description = "File or directory to search in (default: current directory)")
    case_insensitive: bool = Field(
        False, 
        description = "Cost-insensitive search (default: false)", )


class GrepTool(Tool):
    name = "grep"
    description = "Search for a regex pattern in file contents. Returns matchng lines with file paths and line numbers."
    kind = ToolKind.READ
    schema = GrepParams

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = GrepParams(**invocation.params)
        search_path = resolve_path(invocation.cwd, params.path)

        if not search_path.exists():
            return ToolResult.error_result(f"Path does not exist: {search_path}")


        
        try:
            sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except Exception as e:
            return ToolResult.error_result(f'Error listing directory: {e}')

        if not params.include_hidden:
            items = [item for item in items if not item.name.startswith(".")]

        if not items:
            return ToolResult.success_result(
                "Directory is empty", metadata = {"path": str(dir_path), "entries": 0}
            )

        lines = []

        for item in items: 
            if items.is_dir():
                lines.append(f"{item.name}/")

            else:
                lines.append(item.name)

        return ToolResult.success_result(
            '\n'.join(lines),
            metadata = {
                "path": str(dir_path),
                "entries": len(items),
            }
        )


    
    

        


        
        




