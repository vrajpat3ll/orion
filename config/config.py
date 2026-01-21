import os
from pathlib import Path
from typing import List, Union
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    load_dotenv()
    name: str = os.environ.get(
        "MODEL_ID",
        "mistralai/devstral-2512:free",
    )  # "mistralai/devstral-2512:free"
    # ? use a fairly creative response
    temperature: float = Field(default=1, ge=0.0, le=2.0)
    context_window: Union[int, None] = 256_000


class Config(BaseModel):
    load_dotenv()
    model: ModelConfig = Field(default_factory=ModelConfig)
    cwd: Path = Field(default_factory=Path.cwd)

    # load .env variables here

    # per agent
    max_turns: int = 100

    developer_instructions: Union[str, None] = None
    user_instructions: Union[str, None] = None

    debug: bool = False

    @property
    def api_key(self) -> Union[str, None]:
        return os.environ.get("API_KEY")

    @property
    def base_url(self) -> Union[str, None]:
        return os.environ.get("BASE_URL")

    @property
    def model_name(self) -> str:
        return self.model.name

    @model_name.setter
    def model_name(self, value: str) -> None:
        self.model.name = value

    @property
    def temperature(self) -> float:
        return self.model.temperature

    @temperature.setter
    def temperature(self, value: float) -> None:
        self.model.temperature = value

    def validate(self) -> List[str]:
        errors = []

        if not self.api_key:
            errors.append("No API key found. Set API_KEY environment variable.")

        if not self.cwd.exists():
            errors.append(f"Working directory does not exist: {self.cwd.exists()}")

        return errors
