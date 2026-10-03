from pydantic import BaseModel, Field
from utils import resolve_path
from base import ToolKind, ToolResult

class ReadFileParams(BaseModel):

    path: str = Field(
        ...,
        description = "Path to the file to read"
    )

    offset: int = Field(
        1,
        ge=1,
        description = "Line number to start reading from (1-based), Defaults to 1"
    )

    limit: int | None = Field(
        None,
        ge=1,
        description="Maximum number of lines to read. If not specificed, read all lines from the offset"
    )


class ReadFileTool(Tool):
    name = "read_file"
    description = {
        "Read the contents of a text file. Returns the file content with line number",
        "For larger files, use offset and limit to read specific portions",
        "Cannot read binary files (images, executables, ext.)"
    }

    kind = ToolKind.READ

    schema = ReadFileParams

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = ReadFileParams(**invocation.params)
        path = resolve_path(invocation.cwd, params.path)

        if not path.exists():
            return ToolResult.error_result(f"File not found: {path}")




