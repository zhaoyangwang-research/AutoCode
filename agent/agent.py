from typing import AsyncGenerator
from agent.events import AgentEvent, AgentEventType
from client.llm_client import LLMClient

class Agent:
    def __init__(self):
        self.client = LLMClient()

    async def _agentic_loop(self)-> AsyncGenerator[AgentEvent, None]:

        async for event in self.client.chat_completion(
            messages=[{"role": "user", "content": "Hello, how are you?"}], 
            stream=True):
            print(event)

            





