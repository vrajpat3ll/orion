from datetime import datetime
import json
from typing import Optional
import uuid
from client.llm_client import LLMClient
from config.config import Config
from config.loader import get_data_directory
from context.manager import ContextManager
from tools.registry import create_default_registry


class Session:
    """Everything related to context compression, loop detection, etc."""

    def __init__(
        self,
        config: Config,
        user_memory: Optional[str] = None,
    ) -> None:
        self.session_id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self._turn_count = 0

        self.config = config
        self.client = LLMClient(config=self.config)
        self.tool_registry = create_default_registry(config=config)
        self.context_manager = ContextManager(
            config=config,
            tools=self.tool_registry.get_tools(),
            user_memory=user_memory,
        )

    def increment_turn(self) -> int:
        self._turn_count += 1
        self.updated_at = datetime.now()

        return self._turn_count

    def _load_memory(self) -> Optional[str]:
        data_dir = get_data_directory()
        data_dir.mkdir(parents=True, exist_ok=True)
        path = data_dir / "user_memory.json"
        if not path.exists():
            return None

        try:
            content = path.read_text(encoding="utf-8")
            data = json.loads(content)
            entries = data.get("entries", {})
            if not entries:
                return None

            lines = ["User preferences and notes:"]
            for k, v in entries.items():
                lines.append(f"- [{k}] {v}")

        except Exception:
            return None

        return "\n".join(lines)
