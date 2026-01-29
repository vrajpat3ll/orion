import os
from pathlib import Path
import re
from typing import List
from pydantic import BaseModel, Field
from tools.base import Tool, ToolInvocation, ToolKind, ToolResult
from tools.registry import register_tool
from utils.paths import is_binary_path, resolve_path


class GrepParams(BaseModel):
    pattern: str = Field(
        ...,
        description="The regex pattern to search for.",
    )
    path: str = Field(
        ".",
        description="The file or directory path to search in (default: current directory).",
    )
    case_insensitive: bool = Field(
        False, description="Case-insensitive search (default: false)"
    )


@register_tool
class GrepTool(Tool):
    name = "grep"
    description = "Search for a regex pattern in file contents. Returns matching lines with file paths and line numbers."
    kind = ToolKind.READ
    schema = GrepParams

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = GrepParams(**invocation.params)
        search_path = resolve_path(invocation.cwd, params.path)

        if not search_path.exists():
            return ToolResult.error_result(f"Path does not exist: {search_path}")

        try:
            pattern = re.compile(
                pattern=params.pattern,
                flags=re.IGNORECASE if params.case_insensitive else 0,
            )
        except Exception as e:
            return ToolResult.error_result(f"Invalid regex expression: {e}")
        if search_path.is_dir():
            files = self._find_files(search_path)
        else:
            files = [search_path]

        output_lines = []
        matches = 0
        # ? Limit to 500 files for faster execution
        for file in files[:500]:
            try:
                content = file.read_text(encoding="utf-8")
            except Exception:
                continue
            lines = content.splitlines()
            file_matches = False
            for i, line in enumerate(lines, 1):
                if pattern.search(line):
                    matches += 1
                    if not file_matches:
                        file_matches = True
                    try:
                        rel_path = file.relative_to(invocation.cwd)
                    except Exception:
                        rel_path = file
                    output_lines.append(f"=== {rel_path} ===")

                    output_lines.append(f"{i:>5}|{line}")

            if file_matches:
                output_lines.append("")

        if len(files) > 500:
            output_lines.append("... (limited to 500 files)")

        if not output_lines:
            return ToolResult.success_result(
                f"No matches found for pattern '{params.pattern}'",
                metadata={
                    "path": str(search_path),
                    "matches": matches,
                    "files_searched": len(files),
                },
            )
        return ToolResult.success_result(
            "\n".join(output_lines),
            metadata={
                "path": str(search_path),
                "matches": matches,
                "files_searched": len(files),
            },
        )

    def _find_files(self, path: Path) -> List[Path]:
        files = []
        exclude_dirs_pattern = re.compile(r"\.venv|venv|\.git")
        for root, _, filenames in os.walk(path):
            if re.search(exclude_dirs_pattern, root):
                continue
            for filename in filenames:
                if filename.startswith("."):
                    continue
                file_path = Path(root) / filename
                if not is_binary_path(path=file_path):
                    files.append(file_path)

        return files
