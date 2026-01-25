from pathlib import Path
from typing import Any, Dict, List, Union
from config.config import Config
from tools.base import Tool, ToolInvocation, ToolResult
from tools.builtin import get_all_builtin_tools
from utils.logger import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def regsiter(self, tool: Tool) -> None:
        if tool.name in self._tools:
            logger.warning(f"[register] Overwriting existing tool: {tool.name}")

        self._tools[tool.name] = tool
        logger.info(f"[register] Registered {tool.name} tool to tool registry.")

    def unregsiter(self, name: str) -> bool:
        if name in self._tools.keys():
            del self._tools[name]
            logger.info(f"[unregister] Unregistered {name} tool from tool registry.")
            return True

        logger.info(f"[unregister] Tool not found: {name}")
        return False

    def get(self, name: str) -> Union[Tool, None]:
        if name in self._tools.keys():
            return self._tools[name]
        return None

    def get_tools(self) -> List[Tool]:
        return [tool for tool in self._tools.values()]

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
                error=f"Invalid parameters : {';'.join(validation_errors)}",
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
                f"Internal error: {e}",
                metadata={
                    "tool_name": name,
                },
            )


def create_default_registry(config: Config) -> ToolRegistry:
    registry = ToolRegistry()
    for tool_cls in get_all_builtin_tools():
        registry.regsiter(tool_cls(config=config))
    return registry
