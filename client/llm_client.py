import asyncio
from typing import Any, AsyncGenerator
from openai import AsyncOpenAI

from client.response import StreamEvent, EventType, TextDelta, TokenUsage


class LLMClient:
    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None
        self._max_retries = 3

    def get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=",",
                base_url="https://openrouter.ai/api/v1",
            )
        return self._client

    async def chat_completion(
            self, 
            messages: list[dict[str, Any]],
            stream: bool = True
            ) -> AsyncGenerator[StreamEvent, None]:

            client = self.get_client()
            
            kwargs = {
                "model": "nvidia/nemotron-3.5-lightning:free",
                "messages": messages,
                "stream": stream,
            }

            for attempt in range(self._max_retries + 1):
                try:
                    if stream:
                        async for event in self._stream_response(client, kwargs):
                            yield event
                    else:
                        event = await self._non_stream_response(client, kwargs)
                        yield event 
                    return   
                
                except RateLimitError as e:
                    if attempt < self._max_retries:
                        wait_time = 2**attempt
                        await asyncio.sleep(wait_time)
                    else:
                        yield StreamEvent(
                            type=EventType.ERROR,
                            error=f"Rate limit exceeded after {self._max_retries} retries: {str(e)}"
                        )
                        return
                    
                except APIError as e:
                    yield StreamEvent(
                        type=EventType.ERROR,
                        error=f"API error: {str(e)}"
                    )
                    return 
                

    
    async def _stream_response(
              self, 
              client: AsyncOpenAI, 
              kwargs: dict[str, Any]
              )-> AsyncGenerator[StreamEvent, None]:
        
        response = await client.chat.completions.create(**kwargs)

        finish_reason: str | None = None
        usage: TokenUsage | None = None

        async for chunk in response:
            if hasattr(chunk, "usage") and chunk.usage:
                usage = TokenUsage(
                    prompt_tokens=chunk.usage.prompt_tokens,
                    completion_tokens=chunk.usage.completion_tokens,
                    total_tokens=chunk.usage.total_tokens,
                    cached_tokens=chunk.usage.prompt_tokens_details.usage.cached_tokens,
                )
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            delta = choice.delta

            if choice.finish_reason:
                finish_reason = choice.finish_reason
            if delta.content:
                yield StreamEvent(
                    type=EventType.TEXT_DELTA,
                    text_delta=TextDelta(content=delta.content),
                    usage=usage)
                

         
    async def _non_stream_response(self, client: AsyncOpenAI, kwargs: dict[str, Any],
                                   ):
        response = await client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        message = choice.message

        text_delta = None

        if message.content:
            text_delta = TextDelta(content=message.content)

        usage = None

        if response.usage:
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                cached_tokens=response.usage.prompt_tokens_details.usage.cached_tokens,
            )
        return StreamEvent(
                type=EventType.Message_COMPLETE,
                text_delta=text_delta,
                finish_reason=choice.finish_reason,
        )
            