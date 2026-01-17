from agent.agent import Agent
from agent.events import AgentEventType
from ui.tui import TUI, get_console
from typing import Union
from utils.logger import get_logger

console = get_console()
logger = get_logger(__name__)


class CLI:
    def __init__(self) -> None:
        self.agent: Union[Agent, None] = None
        self.tui = TUI(console)

    async def run_single(self, message: str) -> Union[str, None]:
        async with Agent() as agent:
            self.agent = agent
            logger.info("[run_single] Initialized agent")
            return await self._process_message(message)

    async def run_interactive(self):
        try:
            async with Agent() as agent:
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

                case AgentEventType.AGENT_ERROR:
                    error = event.data.get("error", "Unknown error")
                    console.print(f"\n[error]{error}\n[/error]")
                    logger.error(error)

        return final_response
