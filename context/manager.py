from typing import Any, Dict, List, Union
from dataclasses import dataclass

from prompts import get_system_prompt
from utils.text import estimate_tokens#, count_tokens


@dataclass
class LLMMessage:
    role: str
    content: str
    token_count: Union[int, None]

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "role": self.role,
        }
        if self.content:
            result["content"] = self.content

        return result


class ContextManager:
    def __init__(self) -> None:
        self._system_prompt = get_system_prompt()
        # ? need model name to actually count tokens, maybe use a global config
        self._model_name = ""
        self._messages: List[LLMMessage] = []

    def add_user_message(self, message: str):
        item = LLMMessage(
            role="user",
            content=message,
            # token_count=count_tokens(message, config.currently_used_model_name),
            token_count=estimate_tokens(message),
        )
        self._messages.append(item)

    def add_assistant_message(self, message: str):
        item = LLMMessage(
            role="assistant",
            content=message or "",
            # token_count=count_tokens(message, config.currently_used_model_name),
            token_count=estimate_tokens(message),
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


if __name__ == "__main__":
    from pprint import pprint

    CtxMgr = ContextManager()
    CtxMgr.add_user_message("Hi!")
    CtxMgr.add_assistant_message("Hi, how are you?")

    pprint(CtxMgr.get_messages())
