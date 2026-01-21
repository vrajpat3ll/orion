import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Union
from rich import box
from rich.console import Console, Group
from rich.theme import Theme
from rich.rule import Rule
from rich.text import Text
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from utils.paths import display_path_rel_to_cwd
from utils.text import truncate_text


AGENT_THEME = Theme(
    {
        # General
        "info": "cyan",
        "error": "red bold",
        "warning": "bright_red bold",
        "success": "green",
        "dim": "dim",
        "muted": "grey50",
        "border": "grey35",
        "highlight": "bold cyan",
        # Roles
        "user": "bright_blue bold",
        "assistant": "bright_white",
        # Tools
        "tool": "bright_magenta bold",
        "tool.read": "cyan",
        # Code / Blocks
        "code": "white",
    }
)

_console: Union[Console, None] = None


def get_console() -> Console:
    global _console
    if _console is None:
        # TODO: check for highlight=True
        _console = Console(theme=AGENT_THEME, highlight=False)
    return _console


class TUI:
    def __init__(self, console: Union[Console, None] = None) -> None:
        self.console = console or get_console()
        self._assistant_stream_open = False
        self._tool_args_by_call_id: Dict[str, Dict[str, Any]] = {}
        self._cwd = Path.cwd()  # TODO: get from global config

    def begin_assistant(self) -> None:
        self.console.print()
        self.console.print(Rule(Text("Assistant", style="assistant")))
        self._assistant_stream_open = True

    def end_assistant(self) -> None:
        if self._assistant_stream_open:
            self.console.print()
            # self.console.print(Rule(Text("Assistant", style="assistant")))
        self._assistant_stream_open = False

    def stream_assistant_delta(self, content: str) -> None:
        self.console.print(content, end="", markup=False)

    def _ordered_args(self, tool_name: str, args: Dict[str, Any]) -> List[tuple]:
        _PREFERRED_ORDER = {
            "read_file": ["path", "offset", "limit"],
        }

        preferred = _PREFERRED_ORDER.get(tool_name, [])
        order: List[Tuple[str, Any]] = []
        seen: Set[str] = set()
        for key in preferred:
            if key in args:
                order.append((key, args.get(key)))
                seen.add(key)

        remaining_keys = set(args.keys() - seen)
        order.extend((key, args[key]) for key in remaining_keys)

        return order

    def _render_args_table(self, tool_name: str, args: Dict[str, Any]) -> Table:
        table = Table.grid(padding=(0, 1))
        table.add_column(style="muted", justify="right", no_wrap=True)
        table.add_column(style="code", overflow="fold")

        for k, v in self._ordered_args(tool_name, args):
            table.add_row(str(k), str(v))

        return table

    def tool_call_start(
        self,
        call_id: str,
        name: str,
        tool_kind: Union[str, None],
        arguments: Dict[str, Any],
    ) -> None:
        self._tool_args_by_call_id[call_id] = arguments
        border_style = f"tool.{tool_kind}" if tool_kind else "tool"

        title = Text.assemble(
            ("• ", "muted"),
            (name, "tool"),
            ("  ", "muted"),
            (f"#{call_id}", "muted"),
        )

        display_args = dict(arguments)
        for key in ("path", "cwd"):
            val = display_args.get(key)
            if isinstance(val, str):
                # display_args[key] = str(resolve_path(base=self._cwd, path=val))
                display_args[key] = display_path_rel_to_cwd(val, self._cwd)

        panel = Panel(
            renderable=self._render_args_table(name, display_args)
            if display_args
            else Text("(no args)", style="muted"),
            title=title,
            title_align="left",
            border_style=border_style,
            padding=(1, 2),
            box=box.ROUNDED,
            subtitle=Text("running", style="muted"),
            subtitle_align="right",
        )
        self.console.print()
        self.console.print(panel)

    def _extract_read_file_code(self, text: str) -> Union[Tuple[int, str], None]:
        """Showing lines start-end of total_lines

        \\s+\\d+|[content]\\n
        """
        body = text
        header_match = re.match(r"^Showing lines (\d+)-(\d+) of (\d+)\n\n", text)
        if header_match:
            body = text[header_match.end() :]

        code_lines: List[str] = []
        start_line: int = -1

        for line in body.splitlines():
            m = re.match(r"\s*(\d+)\|(.*)", line)
            if not m:
                return None

            line_number = int(m.group(1))
            code = m.group(2)

            if start_line == -1:
                start_line = line_number

            code_lines.append(code)

        return start_line, "\n".join(code_lines)

    def tool_call_complete(
        self,
        call_id: str,
        name: str,
        success: bool,
        output: str,
        error: Union[str, None],
        metadata: Dict[str, Any],
        truncated: bool,
    ) -> None:
        border_style = "success" if success else "error"
        status_icon = "✓" if success else "✗"
        status_style = "success" if success else "error"

        title = Text.assemble(
            (f"{status_icon} ", status_style),
            (name, "tool"),
            ("  ", "muted"),
            (f"#{call_id}", "muted"),
        )
        primary_path = None
        blocks = []
        if isinstance(metadata, Dict) and isinstance(metadata.get("path"), str):
            primary_path = metadata.get("path")

        # TODO: carefully remove the errors
        if name == "read_file" and success:
            if primary_path:
                op = self._extract_read_file_code(output)
                start_line = op[0] if op else 1
                code = op[1] if op else ""
                shown_start = metadata.get("shown_start")
                shown_end = metadata.get("shown_end")
                total_lines = metadata.get("total_lines")
                pl = self._guess_programming_lang(primary_path)
                header_parts = [display_path_rel_to_cwd(primary_path, self._cwd)]
                header_parts.append(" • ")
                if shown_start and shown_end and total_lines:
                    header_parts.append(
                        f"Showing lines {shown_start}-{shown_end} of {total_lines}"
                    )

                header = "".join(header_parts)
                blocks.append(Text(header, style="muted"))
                blocks.append(
                    Syntax(
                        code or "",
                        pl,
                        start_line=start_line or 1,
                        theme="monokai",
                        line_numbers=True,
                        word_wrap=False,
                    )
                )
            else:
                output_display = truncate_text(output, "", 250)
                blocks.append(
                    Syntax(
                        output_display,
                        "text",
                        theme="monokai",
                        word_wrap=False,
                    )
                )
        if truncated:
            blocks.append(Text("note: tool output was truncated", style="warning"))

        if error:
            print(error)
            blocks.append(Text(str(error), style="dim"))

        panel = Panel(
            renderable=Group(*blocks),
            title=title,
            title_align="left",
            border_style=border_style,
            padding=(1, 2),
            box=box.ROUNDED,
            subtitle=Text("done" if success else "failed", style=status_style),
            subtitle_align="right",
        )
        self.console.print()
        self.console.print(panel)

    def _guess_programming_lang(self, path: Union[str, None]) -> str:
        if not path:
            return "text"
        suffix = Path(path).suffix.lower()

        return {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "jsx",
            ".ts": "typescript",
            ".tsx": "tsx",
            ".json": "json",
            ".toml": "toml",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".md": "markdown",
            ".sh": "bash",
            ".bash": "bash",
            ".zsh": "bash",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
            ".kt": "kotlin",
            ".swift": "swift",
            ".h": "c",
            ".c": "c",
            ".hpp": "cpp",
            ".cpp": "cpp",
            ".css": "css",
            ".html": "html",
            ".xml": "xml",
            ".sqp": "sqp",
        }.get(suffix, "text")
