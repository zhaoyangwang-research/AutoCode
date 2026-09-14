import re
from typing import Any, AsyncGenerator
from openai import AsyncOpenAI

from client.response import StreamEvent, EventType, TextDelta, TokenUsage


class LLMClient:
    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None

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
        stream: bool = True,
    ) -> AsyncGenerator[StreamEvent, None]:
        client = self.get_client()
        kwargs = {
            "model": "nvidia/nemotron-3.5-lightning:free",
            "messages": messages,
            "stream": stream,
        }

        if stream:
            async for event in self._stream_response(client, kwargs):
                yield event
        else:
            event = await self._non_stream_response(client, kwargs)
            yield event

    async def _stream_response(
        self, client: AsyncOpenAI, kwargs: dict[str, Any]
    ) -> AsyncGenerator[StreamEvent, None]:
        response = await client.chat.completions.create(**kwargs)
        async for chunk in response:
            yield chunk

    async def _non_stream_response(
        self, client: AsyncOpenAI, kwargs: dict[str, Any]
    ) -> StreamEvent:
        response = await client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        message = choice.message

        text_delta = None
        if getattr(message, "content", None):
            text_delta = TextDelta(content=message.content)

        usage = None
        if getattr(response, "usage", None):
            ru = response.usage
            prompt_tokens = getattr(ru, "prompt_tokens", 0)
            completion_tokens = getattr(ru, "completion_tokens", 0)
            total_tokens = getattr(ru, "total_tokens", 0)
            cached_tokens = 0
            if getattr(ru, "prompt_tokens_details", None) and getattr(
                ru.prompt_tokens_details, "usage", None
            ):
                cached_tokens = getattr(ru.prompt_tokens_details.usage, "cached_tokens", 0)
            usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cached_tokens=cached_tokens,
            )

        return StreamEvent(
            type=EventType.MESSAGE_COMPLETE,
            text_delat=text_delta,
            finish_reason=getattr(choice, "finish_reason", None),
            usage=usage,
        )
