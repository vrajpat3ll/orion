from __future__ import annotations
from typing import AsyncGenerator, Union
from agent.events import AgentEvent, AgentEventType
from client.llm_client import LLMClient
from client.reponse import StreamEventType
from context.manager import ContextManager


class Agent:
    def __init__(
        self,
    ) -> None:
        self.client = LLMClient()
        self.context_manager = ContextManager()

    async def run(self, message: str):
        yield AgentEvent.agent_start(message)
        self.context_manager.add_user_message(message)

        usage: Union[str, None] = None
        final_response: Union[str, None] = None
        async for event in self._agentic_loop():
            yield event
            match event.type:
                case AgentEventType.TEXT_COMPLETE:
                    event.data
                    final_response = event.data.get("content", "")

                    if final_response:
                        AgentEvent.text_complete(final_response)

                    # TODO: usage to be added

        yield AgentEvent.agent_end(
            response=final_response,
            usage=usage,
        )

    async def _agentic_loop(self) -> AsyncGenerator[AgentEvent]:
        response_text = ""
        async for event in self.client.chat_completion(
            self.context_manager.get_messages(), stream=True
        ):
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

        self.context_manager.add_assistant_message(response_text)
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
