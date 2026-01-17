from typing import List, Union
from pydantic import BaseModel, Field

from tools.base import Tool, ToolInvocation, ToolKind, ToolResult
from utils.paths import is_binary_path, resolve_path
from utils.text import count_tokens, truncate_text


class ReadFileParams(BaseModel):
    path: str = Field(
        ...,
        description="Path to the file to read (relative to working directory or absolute path)",
    )
    offset: int = Field(
        1,
        ge=1,
        description="Line number to start reading from (1-based). Defaults to 1.",
    )

    limit: Union[int, None] = Field(
        None,
        ge=1,
        description="Maximum number of lines to read. If not specified, reads entire file.",
    )


class ReadFileTool(Tool):
    name = "read_file"
    description = (
        "Read the contents of a text file. Returns the file content with line numbers. "
        "For large files, use offset and limit to read specific portions. "
        "Cannot read binary files (images, executables, etc.)."
    )
    kind = ToolKind.READ
    schema = ReadFileParams

    MAX_FILE_SIZE = 10 * (1 << 20)  # ? 10MB
    MAX_OUTPUT_TOKENS = 25_000

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = ReadFileParams(**invocation.params)
        path = resolve_path(invocation.cwd, params.path)

        if not path.exists():
            return ToolResult.error_result(error=f"File not found: {path}")

        if not path.is_file():
            return ToolResult.error_result(error=f"Not a file: {path}")

        # ? Do not want to contaminate context if the file is too large
        file_size = path.stat().st_size
        if file_size >= self.MAX_FILE_SIZE:
            return ToolResult.error_result(
                f"File too large ({file_size >> 20:.1f} MB). "
                f"Maximum supported is {self.MAX_FILE_SIZE >> 20:.1f}MB."
            )

        if is_binary_path(path):
            file_size_mb = file_size >> 20
            human_readable_file_size = (
                f"{file_size_mb:.2f}MB" if file_size_mb >= 1 else f"{file_size} bytes"
            )

            return ToolResult.error_result(
                f"Cannot read binary file: {path} ({human_readable_file_size}). "
                f"This tool only reads text files."
            )

        try:
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = path.read_text(encoding="latin-1")

            lines = content.splitlines()
            total_lines = len(lines)

            if total_lines == 0:
                return ToolResult.success_result(
                    "File is empty.",
                    metadata={
                        "lines": 0,
                    },
                )
            start_idx = max(0, params.offset - 1)  # ? 1-based offset, remember?
            if params.limit is not None:
                end_idx = min(start_idx + params.limit, total_lines)
            else:
                end_idx = total_lines

            selected_lines = lines[start_idx:end_idx]
            formatted_lines: List[str] = []
            for i, line in enumerate(selected_lines):
                formatted_lines.append(f"{i + 1:>5}|{line}")

            model = "mistralai/devstral-2512:free"
            output = "\n".join(formatted_lines)
            token_count = count_tokens(output, model)

            truncated = False
            if token_count > self.MAX_OUTPUT_TOKENS:
                output = truncate_text(
                    output,
                    model,
                    max_tokens=self.MAX_OUTPUT_TOKENS,
                    suffix=f"\n... [truncated {total_lines} total lines]",
                )
                truncated = True
            metadata_lines = []
            if start_idx > 0 or end_idx < total_lines:
                metadata_lines.append(
                    f"Showing lines {start_idx + 1}-{end_idx} of {total_lines}"
                )
            if metadata_lines:
                header = " | ".join(metadata_lines) + "\n\n"
                output = header + output

            return ToolResult.success_result(
                output,
                truncated=truncated,
                metadata={
                    "path": str(path),
                    "total_lines": total_lines,
                    "shown_start": start_idx + 1,
                    "shown_end": end_idx,  # ? end_idx is 1-based
                },
            )

        except Exception as e:
            return ToolResult.error_result(error=f"Failed to read file: {e}")
