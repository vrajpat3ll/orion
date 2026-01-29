from pydantic import BaseModel, Field
from tools.base import Tool, ToolInvocation, ToolKind, ToolResult
from utils.paths import resolve_path


class ListDirParams(BaseModel):
    path: str = Field(
        default=".",
        description="Directory path to list (default: current directory)",
    )
    include_hidden: bool = Field(
        default=False,
        description="Whether to include hidden files and directories (default: false)",
    )
    # TODO: could add recurse: bool = False to recursively list the directory


class ListDirTool(Tool):
    name = "list_dir"
    description = "List the content of a directory."
    kind = ToolKind.READ
    schema = ListDirParams

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = ListDirParams(**invocation.params)

        dir_path = resolve_path(invocation.cwd, params.path)
        if not dir_path.is_dir():
            return ToolResult.error_result(f"{dir_path} is not a directory!")

        if not dir_path.exists():
            return ToolResult.error_result(f"Directory does not exist: {dir_path}")
        try:
            items = sorted(
                dir_path.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )
        except Exception as e:
            return ToolResult.error_result(f"Error listing directory: {e}")

        if not params.include_hidden:
            items = [item for item in items if not item.name.startswith(".")]

        if not items:
            ToolResult.success_result(
                "Directory is empty",
                metadata={
                    "path": dir_path,
                    "entries": 0,
                },
            )
        lines = []
        for item in items:
            if item.is_dir():
                lines.append(f"{item.name}/")
            else:
                lines.append(f"{item.name}")
        output = "\n".join(lines)

        return ToolResult.success_result(
            output=output,
            metadata={
                "path": dir_path.name,
                "entries": len(items),
            },
        )
