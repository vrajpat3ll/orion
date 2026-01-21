from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Any, Dict, Union


@dataclass
class TextDelta:
    content: str

    def __str__(self) -> str:
        return self.content


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            cached_tokens=self.cached_tokens + other.cached_tokens,
        )


class StreamEventType(str, Enum):
    TEXT_DELTA = "text_delta"
    MESSAGE_COMPLETE = "message_complete"
    ERROR = "error"

    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_DELTA = "tool_call_delta"
    TOOL_CALL_COMPLETE = "tool_call_complete"


@dataclass
class ToolCallDelta:
    call_id: str
    name: Union[str, None] = None
    arguments_delta: str = ""


@dataclass
class ToolCall:
    call_id: str
    name: Union[str, None] = None
    arguments: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamEvent:
    type: StreamEventType
    text_delta: Union[TextDelta, None] = None
    error: Union[str, None] = None

    tool_call: Union[ToolCall, None] = None
    tool_call_delta: Union[ToolCallDelta, None] = None

    finish_reason: Union[str, None] = None
    usage: Union[TokenUsage, None] = None


@dataclass
class ToolCallResult:
    tool_call_id: str
    content: str
    is_error: bool = False

    def to_openai_message(self) -> Dict[str, Any]:
        return {
            "role": "tool",
            "tool_call_id": self.tool_call_id,
            "content": self.content,
        }


def parse_tool_call_arguments(arguments: str) -> Dict[str, Any]:
    if not arguments:
        return {}
    try:
        return json.loads(arguments)
    except json.JSONDecodeError:
        return {"raw_arguments": arguments}
