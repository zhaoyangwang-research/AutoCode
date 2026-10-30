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

    def _save_memory(self, memory: dict) -> None:
        data_dir = get_data_dir()
        data_dir_mkdir(parents=True. exist_ok=True)
        path = data_dir / "user_memory.json"

        path.write_text(json.dumps(memory, indent=2,ensure_ascii= False))



    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = MemoryParams(**invocation.params)

        if params.action.lower() == "set":
            if not params.key or not params.value:
                return ToolResult.error_result(
                    "'key' and 'value' are required for 'set' action"
                )

            memory = self._load_memory()
            memory["entries"][params.key] = params.values

            self._save_memory(memory)

            return ToolResult.success_result(f"Set memory:{params.key}")

        elif params.action.lower() == "get":
            if not params.get:
                return ToolResult.error_result("'key' required for 'get' action")

            memory = self._load_memory()

            if params.key not in memory.get('entries', {}):
                return ToolResult.success_result(
                    f"Memory not found: {params.key}",
                    metadata = {
                        'found': False,
                    },
                    )
            return ToolResult.success_result(
                f"Memory found: {params.key}: {memory['entries'][params.key]}",

                 metadata = {
                     'found': True,
                     },
                    )

        elif params.action == "delete":
            if not params.key:
                return ToolResult.error_result("'key' required for 'get' action")

            memory = self._load_memory()

            if params.key not in memory.get('entries', {}):
                return ToolResult.success_result(f"Memory not found: {params.key}")

            del memory['entires'][params.key]
            self._save_memory(memory)

        elif params.action == "list":
        
            memory = self._load_memory()
            entries = memory.get('entries', {})

            if not  entries:
                return ToolResult.success_result(
                    f"No memories stored",
                      metadata = {
                                            'found': False,
                                        },)

            lines = ["Stored memories:"]

            for key, value in sorted(entries.items()):
                lines.append(f"{key}:{value}")

            return ToolResult.success_result("\n".join(lines),
                                               metadata = {
                                                                  'found': True,
                                                                  },)

        elif params.action == "clear":
            memory = self._load_memory()
            count = len(memory.get("entries", {}))
            memory["entities"] = {}

            self._save_memory(memory)
            return ToolResult.success_result(f"Cleared {count} memory entries")

        else:
            return ToolResult.error_result(f"Unknown action: {params.action}")

        

        

    

        




