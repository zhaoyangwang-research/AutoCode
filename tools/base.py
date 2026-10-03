import abc
from pydantic import BaseModel, ValidationError
from enum import Enum
from typing import Any
from dataclasses import dataclass, field
from pydantic.json_schema import model_json_schema


class ToolKind(str, Enum):
    READ = "read"
    WRITE = "write"
    SHELL = "shell"
    NETWORK = "network"
    MEMORY = "memory"
    MCP = "mcp"


@dataclass
class ToolInokation:
    params: dict[str, Any]
    cwd: Path


@dataclass
class ToolConfirmation:
    tool_name: str
    params: dict[str, Any]
    description: str




@dataclass
class ToolResults:
    success: bool
    output: str
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)



class Tool(abc.ABC):
    name: str = "base_tool"
    description: str = "Base tool"
    kind: ToolKind = ToolKind.READ

    def __init__(self) -> None:
        pass

    @property
    def schema(self) -> dict[str, Any] | type["BaseModel"]:
        raise NotImplementedError("Tool must define schema property or class atttribute ")

    @abc.abstractmethod
    async  def execute(self, invocation: ToolInocation) -> ToolResult:
        pass

    def validate_params(self, params: dict[str, Any]) -> list[str]:
        schema = self.schema
        if isinstance(schema, type) and issubclass(schema, BaseModel):

            try:
                BaseModel(**params)

            except ValidationError as e:
                errors = []
                for error in e.errors():
                    field = ".".join(str[x] for x i error.get("loc", []))
                    msg = error.get("msg", "Validaton error")
                    errors.append(f"Parameter '{field}': {msg}")
                return errors
            
            except Exception as e:
                return [str(e)]

        return []

#might change states so it triggers confirmation
    def is_mutation(self, params: dict[str, Any]) -> bool:
        return self.kind in {
            ToolKind.WRITE,
            ToolKind.SHELL,
            ToolKind.NETWORK,
            ToolKind.MEMORY, 
        }

    async def get_confirmation(self, invocation: ToolInocation) -> ToolInocation | None:
        if not self.is_mutating(invocation.params):
            return None

        return ToolConfirmation(
            tool_name=self.name, 
            params = invocation.params,
            description=f"Execute {self.name}",
        ) 

    #padynatic convert to Json openai tool request schema format
    def to_openai_schema(self) -> dict[str, Any]:
        schema = self.schema

        if isinstance(schema, type) and issubclass(schema, BaseModel):
            json_schema = model_json_schema(schema, mode = "serialization")

            return {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type":"object",
                    "properties": json_schema.get("properties", {}),
                    "required": json_schema.get("required", []),
                },
            }

        if isinstance(schema, dict):
            result = {
                "name": self.name,
                "description": self.description,
            }

            if "parameters" in schema:
                result["parameters"] = schema["parameters"]
            else:
                result["parameters"] = schema

            return result

        raise ValidationError(f"Invalid schema type for tool {self.name}: {type(schema)}")

    
        








                
                






