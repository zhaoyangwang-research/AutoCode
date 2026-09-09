import re

from openai import AsyncOpenAI
class LLMClient:
    def __init__(self) -> None:
        self._client :  AsyncOpenAI | None = None

    def get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key="," ,
                base_url="https://openrouter.ai/api/v1",
            )  
        return self._client

    async def chat_completion(self, 
                              messages: list[dict[str, Any]],
                              stream: bool = True):
            client = self.get_client()

            kwargs = {
                "model": "nvidia/nemotron-3.5-lightning:free",
                "messages": messages,
                "stream": stream,
            }



            if stream:
                 self._stream_response()
            else:
                 self._non_stream_response(client, kwargs)

    async def _stream_response(self):
         pass

    async def _non_stream_response(self, client: AsyncOpenAI, kwargs: dict[str, Any],
                                   ):
         response = client.chat.completions.create(**kwargs)
         
         
         