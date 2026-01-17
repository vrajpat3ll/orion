from typing import List
from tools.builtin.read_file import ReadFileTool
from tools.base import Tool

__all__ = [
    "ReadFileTool",
]


def get_all_builtin_tools() -> List[type[Tool]]:
    return [
        ReadFileTool,
    ]
