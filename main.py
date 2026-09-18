from client.llm_client import LLMClient
import asyncio

import click

class CLI:
    def __init__(self):
        pass

    def run_single():
        pass 



async def run(messags:dict[str, Any]):
    client = LLMClient()
    async for event in client.chat_completion(messages, stream=True):
        print(event)

@click.command()
@click.argument("prompt", required=False)


def main(
    prompt: str | None = None,
):  
    
    client = LLMClient()
    messages = [
        {"role": "user", "content": "Hello, how are you?"},
    ]

    asyncio.run(run(messages))
    print("Done")
    

asyncio.run(main())