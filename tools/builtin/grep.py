import re
from tools.base import Tool, ToolKind, ToolInvocation, ToolResult
from pydantic import BaseModel, Field
import os
from utils.paths import resolve_path
from pathlib import Path


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
            flags = re.IGNORECASE if params.case_insensitive else 0
            pattern = re.compile(params.pattern, flags)
        except re.error as e:
            return ToolResult.error_result(f"Invalid regex pattern: {e}")

        if search_path.is_dir():
            files = self._find_files(search_path)
        else:
            files = [search_path]

        output_lines = []
        matches = 0

        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8')
            except Exception:
                continue

            lines = content.splitlines()
            file_matches = False

            output_lines = []
            for i, line in lines:
                if pattern.search(line):
                    matches += 1
                    if not file_matches:
                        rel_path = file_path.relative_to(invocation.cwd)
                        output_lines.append(f"=== {rel_path} ===")
                        file_matches = True
                    output_lines.append(f"{i}:{line}")

            if file_matches:
                output_lines.append("")

        if not output_lines:
            return ToolResult.success_result(
                f"No matches found for pattern '{params.pattern}'",
                metadata = {
                    "path": str(search_path),
                    "matches": matches,
                },
            )
        

        return ToolResult.success_result(
            '\n'.join(output_lines),
            metadata = {
                "path": str(search_path),
                "matches": matches,
            }
        )

    def _find_files(self, search_path: Path) -> list[Path]:
        files = []
        for root, dirs, filenames in os.walk(search_path):
            for filename in filenames:
                if filename.startwith('.'):
                    continue
                file_path = Path(root) / filename
                if not is_binary_file(file_path):
                    files.append(file_path)
                    if len(files) >= 500:
                        return files

        return files 
        
            



    


        



    
    

        


        
        




