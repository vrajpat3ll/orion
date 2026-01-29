import os
from pathlib import Path
import re
from typing import List
from pydantic import BaseModel, Field
from tools.base import Tool, ToolInvocation, ToolKind, ToolResult
from tools.registry import register_tool
from utils.paths import is_binary_path, resolve_path


class GlobParams(BaseModel):
    pattern: str = Field(
        ...,
        description="Glob pattern to match.",
    )
    path: str = Field(
        ".",
        description="Directory to search in (default: current directory).",
    )


@register_tool
class GlobTool(Tool):
    name = "glob"
    description = (
        "Find files matching a glob pattern. Supports `**` for recursive matching."
    )
    kind = ToolKind.READ
    schema = GlobParams

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = GlobParams(**invocation.params)
        search_path = resolve_path(invocation.cwd, params.path)

        if not search_path.exists() or not search_path.is_dir():
            return ToolResult.error_result(f"Directory does not exist: {search_path}")

        try:
            matches = list(search_path.glob(params.pattern))
            matches = [f for f in matches if f.is_file()]
        except Exception as e:
            return ToolResult.error_result(f"Error searching: {e}")

        output_lines = []
        for file in matches[:1000]:
            try:
                rel_path = file.relative_to(invocation.cwd)
            except Exception:
                rel_path = file
                output_lines.append(str(rel_path))
        if len(matches) > 1000:
            output_lines.append("... (limited to 1000 results)")

        if not output_lines:
            return ToolResult.success_result(
                f"No matches found for pattern '{params.pattern}'",
                metadata={
                    "path": str(search_path),
                    "matches": len(matches),
                },
            )
        return ToolResult.success_result(
            "\n".join(output_lines),
            metadata={
                "path": str(search_path),
                "matches": len(matches),
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
