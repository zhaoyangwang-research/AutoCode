import abc
from pydantic import BaseModel
from enum import Enum
from typing import Any
from dataclasses import dataclass


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
    async  def execute(self, invocation: ToolInokation) -> ToolResult:
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

#might change states
    def is_mutation(self, params: dict[str, ANy]) -> bool:
        return self.kind in {
            ToolKind.WRITE,
            ToolKind.SHELL,
            ToolKind.NETWORK,
            ToolKind.MEMORY, 
        }
                
                






