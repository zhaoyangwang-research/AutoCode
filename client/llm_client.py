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

    def _build_tools(self, tools: list[dict[str, Any]]):
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get(
                        "parameters",
                        {
                            "type": "object",
                            "properties": {}
                        },
                    ),
                },
            }
            for tool in tools
        ]

    async def chat_completion(
            self, 
            messages: list[dict[str, Any]],
            tools: list[dict[str, Any]] | None = None,
            stream: bool = True
            ) -> AsyncGenerator[StreamEvent, None]:

            client = self.get_client()
            
            kwargs = {
                "model": "nvidia/nemotron-3.5-lightning:free",
                "messages": messages,
                "stream": stream,
            }

            if tools:
                kwargs['tools'] = self._build_tools(tools)
                kwargs["tool_choice"] = "auto"

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
        tool_calls: dict[int, dict[str, Any]] = {}

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
            if delta.tool_calls:
                for tool_call_delta in delta.tool_calls:
                    idx = tool_call_delta.index

                    if idx in tool_calls:
                        tool_calls[idx] = {
                            'id': tool_call_delta.id or "",
                            'name': '',
                            'arguments': ''
                        }

                        if tool_call_delta.function:
                            if tool_call_delta.function.name:
                                tool_calls[idx]['name'] = tool_call_delta.function.name
                                yield StreamEvent(
                                    type=StreamEventType.TOOL_CALL_START,
                                    tool_call_delta = ToolCallDelta(
                                        call_id=tool_calls[idx]['id'],
                                        name = tool_call_delta.function.name,
                                    ),
                                )

                            if tool_call_delta.function.arguments:
                                tool_calls[idx]['arguments'] += tool_call_delta.function.arguments
                                yield StreamEvent(
                                    type=StreamEventType.TOOL_CALL_DELTA.
                                    tool_call_delta=ToolCallDelta(
                                        call_id=tool_calls[idx]["id"],
                                        name = tool_call_delta.function.name,   
                                        arguments_delta = tool_call_delta.function.arguments,    
                                    ),
                                )
            for idx, tc in tool_calls.items():
                yield StreamEvent(
                    type=StreamEventType.MESSAGE_COMPLETE,
                    tool_call = ToolCall(
                        call_id=tc['id'],
                        name=tc['name'],
                        arguments= parse_tool_call_arguments(tc["arguments"]), 
                    ), 
                )
            

            

            
            
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
            