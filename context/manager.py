from typing import Any, Dict, List, Union
from dataclasses import dataclass, field

from config.config import Config
from prompts import get_system_prompt
from utils.text import count_tokens


@dataclass
class LLMMessage:
    role: str
    content: str
    tool_call_id: Union[str, None] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)

    token_count: Union[int, None] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "role": self.role,
        }
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        if self.content:
            result["content"] = self.content
        result["content"] = self.content or ""

        return result


class ContextManager:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._system_prompt = get_system_prompt(config)
        self._messages: List[LLMMessage] = []

    def add_user_message(self, message: str):
        item = LLMMessage(
            role="user",
            content=message or "",
            token_count=count_tokens(message, self.config.model_name),
        )
        self._messages.append(item)

    def add_assistant_message(
        self,
        message: str,
        tool_calls: Union[List[Dict[str, Any]], None] = None,
    ):
        item = LLMMessage(
            role="assistant",
            content=message or "",
            tool_calls=tool_calls or [],
            token_count=count_tokens(message, self.config.model_name),
        )
        self._messages.append(item)

    def add_tool_result(self, tool_call_id: str, message: str) -> None:
        item = LLMMessage(
            role="tool",
            content=message,
            tool_call_id=tool_call_id,
            token_count=count_tokens(message or "", self.config.model_name),
        )
        self._messages.append(item)

    def get_messages(self) -> List[Dict[str, Any]]:
        messages = []
        if self._system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": self._system_prompt,
                }
            )

        for item in self._messages:
            messages.append(item.to_dict())

        return messages


# if __name__ == "__main__":
#     from pprint import pprint

#     CtxMgr = ContextManager(config=Config())
#     CtxMgr.add_user_message("Hi!")
#     CtxMgr.add_assistant_message("Hi, how are you?")

#     pprint(CtxMgr.get_messages())
