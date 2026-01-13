import asyncio
from typing import Any, Dict, List, Union
import click
from client.client import LLMClient


async def run(messages: List[Dict[str, Any]]):
    client = LLMClient()
    async for event in client.chat_completion(messages, stream=False):
        print(event)


@click.command()
@click.argument("prompt", required=False)
def main(prompt: Union[str, None]):
    print("Hello from orion!")
    messages = [{"role": "user", "content": prompt}]
    asyncio.run(run(messages))


if __name__ == "__main__":
    asyncio.run(main())
