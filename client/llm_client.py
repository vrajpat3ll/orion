import asyncio
import os

# to get asynchronous messages
from openai import APIConnectionError, AsyncOpenAI, RateLimitError
from typing import Any, AsyncGenerator, Dict, List, Union
from dotenv import load_dotenv

from client.reponse import StreamEventType, StreamEvent, TextDelta, TokenUsage


class LLMClient:
    def __init__(self) -> None:
        self._client: Union[AsyncOpenAI, None] = None
        self._max_retries: int = 3
        load_dotenv()

    def get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=os.environ.get(
                    "OPENROUTER_API_KEY"
                ),  # use *_API_KEY for this param
                base_url="https://openrouter.ai/api/v1/",  # use BASE_URL env variable later on
                # max_retries=0,  # set later to something reasonable, default is 2
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    async def chat_completion(
        self, messages: List[Dict[str, Any]], stream: bool = True
    ) -> AsyncGenerator[StreamEvent, None]:
        """create a completion of the messages given

        Args:
            messages (List[Dict[str, Any]]): List of messages
            stream (bool, optional): Yield a streaming repsonse for completion. Defaults to True.
        """
        client = self.get_client()
        kwargs = {
            "model": "mistralai/devstral-2512:free",
            "messages": messages,
            "stream": stream,
        }
        # exponential backoff retrying
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
                    wait_time = 2**attempt  # retry after 1s, 2s, 4s, ...
                    await asyncio.sleep(wait_time)
                else:
                    yield StreamEvent(
                        type=StreamEventType.ERROR, error=f"Rate limit exceeded: {e}"
                    )
                    return
            except APIConnectionError as e:
                if attempt < self._max_retries:
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                else:
                    yield StreamEvent(
                        type=StreamEventType.ERROR, error=f"Connection error: {e}"
                    )
                    return

    async def _stream_response(
        self, client: AsyncOpenAI, kwargs: Dict[str, Any]
    ) -> AsyncGenerator[StreamEvent, None]:
        response = await client.chat.completions.create(**kwargs)

        usage: Union[TokenUsage, None] = None
        finish_reason: Union[str, None] = None
        async for chunk in response:
            if hasattr(chunk, "usage") and chunk.usage:
                usage = TokenUsage(
                    prompt_tokens=chunk.usage.prompt_tokens,
                    completion_tokens=chunk.usage.completion_tokens,
                    total_tokens=chunk.usage.total_tokens,
                    cached_tokens=chunk.usage.prompt_tokens_details.cached_tokens,
                )

            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = choice.delta
            if choice.finish_reason:
                finish_reason = choice.finish_reason

            if delta.content:
                yield StreamEvent(
                    type=StreamEventType.TEXT_DELTA,
                    text_delta=TextDelta(delta.content),
                )

        yield StreamEvent(
            type=StreamEventType.MESSAGE_COMPLETE,
            finish_reason=finish_reason,
            usage=usage,
        )

    async def _non_stream_response(
        self, client: AsyncOpenAI, kwargs: Dict[str, Any]
    ) -> StreamEvent:
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
                cached_tokens=response.usage.prompt_tokens_details.cached_tokens,
            )
        # print(response)
        return StreamEvent(
            type=StreamEventType.MESSAGE_COMPLETE,
            text_delta=text_delta,
            finish_reason=choice.finish_reason,
            usage=usage,
        )
