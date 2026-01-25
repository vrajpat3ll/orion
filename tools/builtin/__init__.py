from typing import List
from tools.builtin.edit_file import EditFileTool
from tools.builtin.read_file import ReadFileTool
from tools.builtin.write_file import WriteFileTool
from tools.base import Tool

__all__ = [
    "ReadFileTool",
    "WriteFileTool",
    "EditFileTool",
]


def get_all_builtin_tools() -> List[type[Tool]]:
    return [
        ReadFileTool,
        WriteFileTool,
        EditFileTool,
    ]
