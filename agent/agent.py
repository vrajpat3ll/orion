from __future__ import annotations
from typing import Any, AsyncGenerator, Dict, List
from agent.events import AgentEvent, AgentEventType
from client.llm_client import LLMClient
from client.reponse import StreamEventType


class Agent:
    def __init__(
        self,
    ) -> None:
        self.client = LLMClient()
        self._context: List[Dict[str, Any]] = []
        # TODO: use a manager instead of keeping everything here
        # self._context_mgr = ContextManager()

    async def run(self, message: str):
        self._context = [{"role": "user", "content": message}]

        yield AgentEvent.agent_start(message)
        # TODO: add user message to context

        usage = None
        final_response = None
        async for event in self._agentic_loop():
            yield event
            match event.type:
                case AgentEventType.TEXT_COMPLETE:
                    event.data
                    final_response = event.data.get("content", "")
                    # TODO: usage to be added
                    AgentEvent.text_complete(final_response)

        yield AgentEvent.agent_end(
            response=final_response,
            usage=usage,
        )

    async def _agentic_loop(self) -> AsyncGenerator[AgentEvent]:
        messages = self._context

        response_text = ""
        async for event in self.client.chat_completion(messages, stream=True):
            match event.type:
                case StreamEventType.TEXT_DELTA:
                    if event.text_delta:
                        content = event.text_delta.content
                        response_text += content
                        yield AgentEvent.text_delta(content)

                case StreamEventType.ERROR:
                    yield AgentEvent.agent_error(
                        event.error or "Unknown error occured."
                    )

        if response_text:
            yield AgentEvent.text_complete(content=response_text)

    # > Methods for context management (_a_sync)
    # ? with Agent() as agent:
    # ?   ...
    async def __aenter__(self) -> Agent:
        return self

    async def __aexit__(
        self,
        exc_type,
        exc_val,
        exc_tb,
    ) -> Agent:
        if self.client:
            await self.client.close()
        return self
