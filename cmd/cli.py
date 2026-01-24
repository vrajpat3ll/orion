from agent.agent import Agent
from agent.events import AgentEventType
from config.config import Config
from ui.tui import TUI, get_console
from typing import Any, Dict, Union
from utils.logger import get_logger

console = get_console()
logger = get_logger(__name__)


class CLI:
    def __init__(self, config: Config, **kwargs: Dict[str, Any]) -> None:
        self.agent: Union[Agent, None] = None
        self.tui = TUI(
            config=config,
            console=console,
        )
        self.config = config
        self.kwargs = kwargs

    async def run_single(self, message: str) -> Union[str, None]:
        async with Agent(self.config) as agent:
            self.agent = agent
            logger.info("[run_single] Initialized agent")
            return await self._process_message(message)

    async def run_interactive(self):
        show_info_card = self.kwargs.get("info", False)
        if isinstance(show_info_card, Dict):
            show_info_card = False
        self.tui.print_welcome(
            title="Config Info Card",
            lines=[
                ["model", f"{self.config.model.name}"],
                ["cwd", f"{self.config.cwd}"],
                ["Available commands", "/help /config /approval /model /exit"],
            ],
            show_info_card=show_info_card,
        )
        try:
            async with Agent(self.config) as agent:
                self.agent = agent
                while True:
                    prompt = None
                    try:
                        prompt = console.input("\n[user]>>[/user] ").strip()
                        if not prompt:
                            continue
                        if prompt in ("/exit", "/bye"):
                            break
                        await self._process_message(prompt)
                    except KeyboardInterrupt:
                        console.print(
                            "[dim]Interrupted. Use /exit or /bye to quit[/dim]"
                        )
                    except EOFError:
                        console.print("[dim]EOF received[/dim]")
                    except Exception:
                        console.print_exception()
        finally:
            console.print("\n[dim]Goodbye![/dim]")

    async def _process_message(self, message: str) -> Union[str, None]:
        if not self.agent:
            logger.info("[cli] agent is None")
            return None

        assistant_streaming = False

        final_response = None
        async for event in self.agent.run(message):
            # print(event)
            match event.type:
                case AgentEventType.TEXT_DELTA:
                    content = event.data.get("content", "")
                    if not assistant_streaming:
                        self.tui.begin_assistant()
                        assistant_streaming = True
                    self.tui.stream_assistant_delta(content)

                case AgentEventType.TEXT_COMPLETE:
                    final_response = event.data.get("content", "")
                    if assistant_streaming:
                        self.tui.end_assistant()
                        assistant_streaming = False

                case AgentEventType.TOOL_CALL_START:
                    tool_name = event.data.get("name", "Unknown Tool")
                    tool = self.agent.session.tool_registry.get(tool_name)
                    tool_kind = None
                    if not tool:
                        return
                    tool_kind = tool.kind.value
                    logger.info(f"{event.data = }, {tool_kind = }")
                    self.tui.tool_call_start(
                        call_id=event.data.get("call_id", ""),
                        name=tool_name,
                        tool_kind=tool_kind,
                        arguments=event.data.get("arguments", {}),
                    )

                case AgentEventType.TOOL_CALL_COMPLETE:
                    tool_call_id = event.data.get("call_id", "Unknown Id")
                    tool_name = event.data.get("name", "Unknown Tool")
                    success = event.data.get("success", "Unknown Status")
                    error = event.data.get("error")
                    metadata = event.data.get("metadata", {})
                    truncated = event.data.get("truncated", False)
                    output = event.data.get("output", "")

                    logger.info(f"[cli] tool call completed, {event = }")
                    self.tui.tool_call_complete(
                        call_id=tool_call_id,
                        name=tool_name,
                        success=success,
                        error=error,
                        metadata=metadata,
                        output=output,
                        truncated=truncated,
                    )

                case AgentEventType.AGENT_ERROR:
                    error = event.data.get("error", "Unknown error")
                    console.print(f"\n[error]{error}\n[/error]")
                    logger.error(error)

        return final_response
