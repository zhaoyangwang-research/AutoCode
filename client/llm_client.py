from openai import AsyncOpenAI
class LLMClient:
    def __init__(self) -> None:
        self._client :  AsyncOpenAI | None = None