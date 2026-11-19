from tools.base import Tool, ToolKind, ToolInvocation, ToolResult
from pydantic import BaseModel, Field

from utils.paths import resolve_path


class WriteFileParams(BaseModel):
    path: str = Field(
        ..., description='Path to the file to write (relative to working direction or absolute )',
    )

    content: str = Field(..., description="Content to write to the file" )

    created_directions: bool = Field(
        True, description = "Create parent directories if they don't exist"
    )

class WriteFileTool(Tool):
    name = "write_file"
    description = {
        "Write content to a file. Creates the file if it doesn't exist"
        "or overwrite if it does. Parent directoris are created automatically"
        "Use this for creating new files or completely replacing file contents "
        "For partial modifications, use the edit tool instead."
    }

    kind = ToolKind.WRITE
    schema = WriteFileParams

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = WriteFileParams(**invocation.params)
        path = resolve_path(invocation.cwd, params.path)

        is_new_file = not path.exists()

        if not is_new_file:
            try:
                old_content = path.read_text(encoding="utf-8")
            except:
                pass




    

         


















 

