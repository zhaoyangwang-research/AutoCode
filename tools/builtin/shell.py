from tools.base import Tool, ToolKind
from pydantic import BaseModel, Field


BLOCKED_COMMANDS = {
    "rm -rf /",
    "rm -rf ~"
}

class ShellParams(BaseModel):
    command: str = Field(..., description= 'The shell command to execute')
    timeout: int = Field(120, ge=1, le=600, description='Timeout in seconds (default:120)')
    cwd: str | None = Field(None, description='working directory for the command')


class ShellTool(Tool):
    name = 'shell'
    kind = ToolKind.SHELL
    description = "Execute a shell command. " \
    "Use this for running system commands, scripts and CLI tools."

    schema = ShellParams

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = ShellParams(**invocation.params)

        command = params.command.lower().strip()
        for blocked in BLOCKED_COMMANDS:
            if blocked in command:
                return ToolResult.error_result(
                    f'Command blocked for safety: {params.command}',
                    metadata = {'blocked': True}
                )

        if params.cwd:
            cwd = Path(params.cwd)
            if not cwd.is_absolute():
                cwd = invocation.cwd / cwd
        else:
            cwd = invocation.cwd

        if not cwd.exists():
            return ToolResult.error_result(f"Working directory doesn't exist: {cwd}")









    


    



