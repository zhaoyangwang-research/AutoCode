from __future__ import annotations
from dataclasses import dataclass, field    
from enum import Enum
from typing import Any

from client.response import TokenUsage


class AgentEventType(str, Enum):
    # Aent lifecycle events
    AGENT_START = "agent_start" 
    AGENT_END = "agent_end"
    AGENT_ERROR = "agent_error"

    # Text streamning
    TEXT_DELTA = "text_delta"
    TEXT_COMPLETE = "text_complete"

@dataclass
class AegntEvent:
    type: AgentEventType
    data: dict[str,] = field(default_factory=dict)

    @classmethod
    def agent_start(cls, message: str) -> AgentEvent:
        return cls(
            type=AgentEventType.AGENT_START, 
            data={"message": message}
            )

    @classmethod
    def agent_end(cls,
                  rssponse: str | None = None,
                  usage: TokenUsage | None = None) -> AgentEvent:
        return cls(
            type=AgentEventType.AGENT_END,
            data={
                "response": rssponse, 
                "usage": usage.__dict__ if usage else None,
                }
        )

    @classmethod
    def agent_error(
        cls, 
        error:str,
        details: dict[str, Any] | None = None,
        ) -> AgentEvent:

        return cls(
            type=AgentEventType.AGENT_ERROR,
            data={"error": error, "details": details or {}  }
        )

    @classmethod
    def text_delta(cls, content:str) -> AgentEvent:
        return cls(
            type=AgentEventType.TEXT_DELTA, 
            data={"content": content}
            )

    @classmethod
    def text_complete(cls, content:str) -> AgentEvent:
        return cls(
            type=AgentEventType.TEXT_COMPLETE, 
            data={"content": content},
            )

    

    



    

    