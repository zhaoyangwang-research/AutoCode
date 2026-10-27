import uuid 
from config.config import Config
from tools.base import Tool, ToolInvocation, ToolKind, ToolResult
from pydantic import BaseModel, Field
from config.loader import get_data_dir
import json

class MemoryParams(BaseModel):
    action : str = Field(
        ..., description="Action: 'set', 'get', 'delete', 'list', 'clear'"
    )

    key: str | None = Field(
        None, description= "Memory key (required for 'set', 'get', 'delete')"
    )

    values: str | None = Field(None, description="Value to store (requireed for 'set', 'get', 'delete') ")



class MemoryTool(Tool):
    name = "memory"
    description = "Store and retrieve persistent memory. Use this to remember user preferens, import contexts or notes."
    kind = ToolKind.MEMORY
    schema = MemoryParams

    def _load_memory(self) -> dict:
        data_dir = get_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        path = data_dir / "user_memory.json"


        if not path.exists():
            return {"entries":{}}
        try:
            content = path.read_text(encoding='utf-8')
            return json.loads(content)
        except Exception:
            return {"entries":{}}


    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = MemoryParams(**invocation.params)

        if params.action.lower() == "set":
            if not params.key or not params.value:
                return ToolResult.error_result(
                    "'key' and 'value' are required for 'set' action"
                )

            self._load_memory
            



