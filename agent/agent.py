from __future__ import annotations
from pathlib import Path
from typing import AsyncGenerator, List, Union
from agent.events import AgentEvent, AgentEventType
from client.llm_client import LLMClient
from client.reponse import StreamEventType, ToolCall, ToolCallResult
from context.manager import ContextManager
from tools.registry import create_default_registry
from utils.logger import get_logger

logger = get_logger(__name__)


class Agent:
    def __init__(
        self,
    ) -> None:
        self.client = LLMClient()
        self.context_manager = ContextManager()
        self.tool_registry = create_default_registry()

    async def run(self, message: str) -> AsyncGenerator[AgentEvent]:
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

        tool_schemas = self.tool_registry.get_schemas()

        tool_calls: List[ToolCall] = []

        async for event in self.client.chat_completion(
            self.context_manager.get_messages(),
            tools=tool_schemas if tool_schemas else None,
            stream=True,
        ):
            match event.type:
                case StreamEventType.TEXT_DELTA:
                    if event.text_delta:
                        content = event.text_delta.content
                        response_text += content
                        yield AgentEvent.text_delta(content)

                case StreamEventType.ERROR:
                    logger.info(
                        f"[agent._agentic_loop] got an error from LLM: {event = }"
                    )
                    yield AgentEvent.agent_error(
                        event.error or "Unknown error occured."
                    )

                case StreamEventType.TOOL_CALL_COMPLETE:
                    if event.tool_call:
                        logger.info(
                            f"[agent._agentic_loop] got a tool_call from LLM: {event.tool_call = }"
                        )
                        tool_calls.append(event.tool_call)

        self.context_manager.add_assistant_message(
            response_text,
            tool_calls=[
                {
                    "id": tc.call_id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": str(tc.arguments),
                    },
                }
                for tc in tool_calls
            ]
            if tool_calls
            else None,
        )
        if response_text:
            yield AgentEvent.text_complete(content=response_text)

        logger.info(f"[agent._agentic_loop] Running {len(tool_calls)} tool_calls")
        tool_call_results: List[ToolCallResult] = []
        for tool_call in tool_calls:
            yield AgentEvent.tool_call_start(
                call_id=tool_call.call_id,
                name=tool_call.name or "",
                arguments=tool_call.arguments,
            )

            result = await self.tool_registry.invoke(
                tool_call.name or "",
                tool_call.arguments,
                Path.cwd(),
            )

            yield AgentEvent.tool_call_complete(
                tool_call.call_id,
                tool_call.name or "",
                result,
            )

            tool_call_results.append(
                ToolCallResult(
                    tool_call_id=tool_call.call_id,
                    content=result.to_model_output(),
                    is_error=not result.success,
                )
            )

        for tool_result in tool_call_results:
            self.context_manager.add_tool_result(
                tool_result.tool_call_id,
                tool_result.content,
            )

    async def __aenter__(self) -> Agent:
        return self

    # > Methods for context management (_a_sync)
    # ? with Agent() as agent:
    # ?   ...

    async def __aexit__(
        self,
        exc_type,
        exc_val,
        exc_tb,
    ) -> Agent:
        if self.client:
            await self.client.close()
        return self
