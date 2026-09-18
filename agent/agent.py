from __future__import annotations
from typing import AsyncGenerator
from agent.events import AgentEvent, AgentEventType
from client.llm_client import LLMClient



class Agent:
    def __init__(self):
        self.client = LLMClient()


    async def run(self, message: str):
        yield AgentEvent.agent_start(message)
        # add user message to context

        async for event in self._agentic_loop():
            yield event

            if event.type == AgentEventType.TEXT_COMPLETE:
                final_response = event.data.get("content")


        yield AgentEvent.agent_enc()




    async def _agentic_loop(self)-> AsyncGenerator[AgentEvent, None]:

        async for event in self.client.chat_completion(
            messages=[{"role": "user", "content": "Hello, how are you?"}]

            response_text = ""


            async for event in self.client,chat_completion(messages, stream=True):
                if event.type == StreamEvetType.TEXT_DELTA:
                    content = event.text_delta.content
                    response_text += content
                    yield AgentEvent.text_delta(content)
                elif event.type == StreamEventType.ERROR:
                    yield AgentEvent.agent_error(event.error or "Unknown error occured")    

            if response_text:
                yield AgentEvent.text_complete(response_text)


            async def __aenter__(self) -> Agent:
                return self
            async def __aexit__(self,
                                exc_type,
                                exc_val,
                                exc_tb, 
            ) -> None:
                if self.client:
                    await self.client.close()
                    self.client = None


            





