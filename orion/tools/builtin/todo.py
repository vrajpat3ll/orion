from typing import Dict, List, Optional
import uuid
from pydantic import BaseModel, Field

from orion.config.config import Config
from orion.tools.base import Tool, ToolInvocation, ToolKind, ToolResult
from orion.tools.registry import register_tool


class ToDoParams(BaseModel):
    action: str = Field(..., description="Action: 'add', 'complete', 'list', 'clear'")
    ids: Optional[List[str]] = Field(
        None, description="List of ToDo IDs (for 'complete' action)"
    )
    contents: Optional[List[str]] = Field(
        None, description="List of ToDo content (for 'add' action)"
    )


@register_tool
class ToDoTool(Tool):
    name = "todos"
    description = "Manage a task list for the current session. Use this to track progress on multi-step tasks."
    kind = ToolKind.MEMORY
    schema = ToDoParams

    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self._todos: Dict[str, str] = {}

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = ToDoParams(**invocation.params)

        action = params.action.lower()
        ids = params.ids
        contents = params.contents
        if action == "add" and ids:
            return ToolResult.error_result("`ids` not allowed for 'add'")

        if action == "complete" and contents:
            return ToolResult.error_result("`contents` not allowed for 'complete'")

        if action not in {"add", "complete", "list", "clear"}:
            return ToolResult.error_result(f"Unknown action: {action}")
        match action:
            case "add":
                if not contents:
                    return ToolResult.error_result(
                        "`contents` are required for 'add' action"
                    )
                output = "Added:"
                for content in contents:
                    todo_id = str(uuid.uuid4())[:8]
                    self._todos[todo_id] = content
                    output += f"\n- [{todo_id}]: {content}"

                return ToolResult.success_result(output)
            case "complete":
                if not ids:
                    return ToolResult.error_result(
                        "`ids` are required for 'complete' action"
                    )
                output_lines = ["Completed:"]
                error_lines = ["Not Found:"]
                for id in ids:
                    if id not in self._todos:
                        error_lines.append(f"- {id}")
                    else:
                        content = self._todos.pop(id)
                        output_lines.append(f"- [{id}]: {content}")

                if len(error_lines) != 1:
                    output_lines.append("")
                    output_lines.extend(error_lines)

                return ToolResult.success_result(output="\n".join(output_lines))
            case "list":
                if not self._todos:
                    return ToolResult.success_result("No ToDos.")
                lines = ["ToDos:"]
                for todo_id, todo in self._todos.items():
                    lines.append(f"  [{todo_id}] {todo}")

                return ToolResult.success_result(output="\n".join(lines))
            case "clear":
                count_todos = len(self._todos)
                self._todos.clear()

                return ToolResult.success_result(output=f"Cleared {count_todos} ToDos.")

        return ToolResult.error_result("[ToDoTool] UNREACHABLE")
