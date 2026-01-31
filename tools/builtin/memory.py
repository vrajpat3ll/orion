from enum import Enum
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from contextlib import suppress

from config.loader import get_data_directory
from tools.base import Tool, ToolInvocation, ToolKind, ToolResult
from tools.registry import register_tool


class Action(str, Enum):
    SET = "set"
    GET = "get"
    DELETE = "delete"
    LIST = "list"
    CLEAR = "clear"


class MemoryParams(BaseModel):
    action: Action = Field(
        ..., description="Action: 'set', 'get', 'delete', 'list', 'clear'"
    )
    keys: Optional[List[str]] = Field(
        None, description="Memory keys (required for {'get', 'set', 'delete'} actions)"
    )
    values: Optional[List[str]] = Field(
        None, description="Values to store (required for 'set' action)"
    )


@register_tool
class MemoryTool(Tool):
    name = "memory"
    description = "Store and retrieve persistent memory. Use this to remember user preferences, important context or notes."
    kind = ToolKind.MEMORY
    schema = MemoryParams

    def _load_memory(self) -> Dict[str, Any]:
        data_dir = get_data_directory()
        data_dir.mkdir(parents=True, exist_ok=True)
        path = data_dir / "user_memory.json"
        if not path.exists():
            return {"entries": {}}
        try:
            content = path.read_text(encoding="utf-8")
            return json.loads(content)
        except Exception as e:
            return {"entries": {}, "error": f"Error while reading {path}: {e}"}

    def _save_memory(self, memory: Dict[str, Any]) -> None:
        data_dir = get_data_directory()
        data_dir.mkdir(parents=True, exist_ok=True)
        path = data_dir / "user_memory.json"

        with suppress(Exception):
            path.write_text(json.dumps(memory, indent=2, ensure_ascii=False))

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = MemoryParams(**invocation.params)

        action = params.action.lower()
        keys = params.keys
        values = params.values

        if action not in Action._member_names_:
            return ToolResult.error_result(f"Unknown action: {action}")

        match action:
            case Action.SET:
                if not values:
                    return ToolResult.error_result(
                        "`values` are required for 'set' action"
                    )
                if not keys:
                    return ToolResult.error_result(
                        "`keys` are required for 'set' action"
                    )
                output = "Added to memory:"
                memory = self._load_memory()
                if memory["error"]:
                    return ToolResult.error_result(f"Error: {memory['error']}")
                for k, v in zip(keys, values):
                    memory["entries"][k] = v
                    output += f"\n- [{k}]: {v}"

                self._save_memory(memory)

                return ToolResult.success_result(output)
            case Action.GET:
                if not keys:
                    return ToolResult.error_result(
                        "`keys` are required for 'get' action"
                    )
                memory = self._load_memory()
                if memory["error"]:
                    return ToolResult.error_result(f"Error: {memory['error']}")

                output_lines = ["Got from memory:"]
                error_lines = ["Not Found:"]
                for k in keys:
                    if k not in memory["entries"]:
                        error_lines.append(f"- {k}")
                    else:
                        content = memory.pop(k)
                        output_lines.append(f"- [{k}]: {content}")

                if len(error_lines) != 1:
                    output_lines.append("")
                    output_lines.extend(error_lines)

                return ToolResult.success_result(
                    output="\n".join(output_lines),
                    metadata={
                        "found": False if error_lines else True,
                    },
                )
            case Action.DELETE:
                if not keys:
                    return ToolResult.error_result(
                        "`keys` are required for 'delete' action"
                    )
                memory = self._load_memory()
                if memory["error"]:
                    return ToolResult.error_result(f"Error: {memory['error']}")

                output_lines = ["Deleted:"]
                error_lines = ["Not found:"]
                for k in keys:
                    v = memory["entries"].pop(k, default="")
                    if not v:
                        error_lines.append(f"\n- {k}")
                if len(error_lines) != 1:
                    output_lines.append("")
                    output_lines.extend(error_lines)

                return ToolResult.success_result(output="\n".join(output_lines))
            case Action.LIST:
                memory = self._load_memory()
                if memory["error"]:
                    return ToolResult.error_result(f"Error: {memory['error']}")
                if not memory["entries"]:
                    return ToolResult.success_result(
                        "No entries in memory.",
                        metadata={
                            "found": False,
                        },
                    )
                lines = ["Stored memories:"]
                for k, v in sorted(memory["entries"].items()):
                    lines.append(f"  [{k}] {v}")

                return ToolResult.success_result(
                    output="\n".join(lines) if len(lines) > 1 else "",
                    metadata={
                        "found": True,
                    },
                )
            case Action.CLEAR:
                memory = self._load_memory()
                memory_count = len(memory["entries"])
                memory = {}
                self._save_memory(memory)
                return ToolResult.success_result(
                    output=f"Cleared {memory_count} memories."
                )

        return ToolResult.error_result("[MemoryTool] UNREACHABLE")
