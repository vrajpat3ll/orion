from pathlib import Path
from typing import Any, Dict, List, Type, Optional

from config.config import Config
from tools.base import Tool, ToolInvocation, ToolResult
from tools.subagents import SubAgentTool, get_default_subagent_definitions
from utils.logger import get_logger

logger = get_logger(__name__)

_TOOL_CLASSES: Dict[str, Type[Tool]] = {}


def register_tool(cls: Type[Tool]):
    """
    Decorator for registering Tool classes.
    Uses tool.name as the unique key.
    """
    name = cls.name
    if name in _TOOL_CLASSES:
        raise ValueError(f"Duplicate tool class registered: {name}")
    _TOOL_CLASSES[name] = cls
    return cls


class ToolRegistry:
    def __init__(self, config: Config) -> None:
        self._tools: Dict[str, Tool] = {}
        self.config = config

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            logger.warning(f"[register] Overwriting existing tool: {tool.name}")

        self._tools[tool.name] = tool
        logger.info(f"[register] Registered {tool.name} tool to tool registry.")

    def unregister(self, name: str) -> bool:
        if name in self._tools:
            del self._tools[name]
            logger.info(f"[unregister] Unregistered {name} tool from tool registry.")
            return True

        logger.info(f"[unregister] Tool not found: {name}")
        return False

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def get_tools(self) -> List[Tool]:
        tools: List[Tool] = list(self._tools.values())
        if self.config.allowed_tools:
            allowed_set = set(self.config.allowed_tools)
            tools = [t for t in tools if t.name in allowed_set]

        return tools

    def get_schemas(self) -> List[Dict[str, Any]]:
        return [tool.to_openai_schema() for tool in self.get_tools()]

    async def invoke(
        self,
        name: str,
        params: Dict[str, Any],
        cwd: Path,
    ) -> ToolResult:
        tool = self.get(name)
        if tool is None:
            return ToolResult.error_result(
                error=f"Unknown Tool: {name}",
                metadata={"tool_name": name},
            )

        validation_errors = tool.validate_params(params)
        if validation_errors:
            return ToolResult.error_result(
                error=f"Invalid parameters: {'; '.join(validation_errors)}",
                metadata={
                    "tool_name": name,
                    "validation_errors": validation_errors,
                },
            )

        invocation = ToolInvocation(
            params=params,
            cwd=cwd,
        )

        try:
            return await tool.execute(invocation)
        except Exception as e:
            logger.exception(f"Tool {name} raised unexpected error: {e}")
            return ToolResult.error_result(
                error=f"Internal error: {e}",
                metadata={"tool_name": name},
            )


def create_default_registry(config: Config) -> ToolRegistry:
    #  to ensure all tools are registered
    import tools.builtin  # noqa: F401

    registry = ToolRegistry(config=config)
    for name, tool_cls in _TOOL_CLASSES.items():
        registry.register(tool_cls(config=config))

    for subagent_def in get_default_subagent_definitions():
        registry.register(SubAgentTool(config, subagent_def))
    return registry
