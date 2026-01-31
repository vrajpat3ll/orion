from pathlib import Path
from tomli import TOMLDecodeError
from typing import Any, Dict, Optional

import tomli
from config.config import Config
from platformdirs import user_config_dir, user_data_dir

from utils.errors import ConfigError
from utils.logger import get_logger

CONFIG_FILE_NAME = "config.toml"
AGENT_FILE_NAME = "AGENTS.md"
logger = get_logger(__name__)


def get_config_directory() -> Path:
    return Path(user_config_dir("orion"))


def get_data_directory() -> Path:
    return Path(user_data_dir("orion"))


def get_system_config_path() -> Path:
    # ~/.config/orion/config.toml
    return get_config_directory() / CONFIG_FILE_NAME


def _get_project_config(cwd: Path) -> Optional[Path]:
    current_dir = cwd.resolve()
    agent_dir = current_dir / ".orion"

    if agent_dir.is_dir():
        config_file = agent_dir / CONFIG_FILE_NAME
        if config_file.exists() and config_file.is_file():
            return config_file.resolve()
    return None


def _get_agent_md_files(cwd: Path) -> Optional[str]:
    current_dir = cwd.resolve()

    if current_dir.is_dir():
        agent_md_file = current_dir / AGENT_FILE_NAME
        if agent_md_file.exists() and agent_md_file.is_file():
            content = agent_md_file.read_text(encoding="utf-8")
            return content
    return None


def _parse_toml(path: Path):
    try:
        pass
        with open(path, "rb") as f:
            return tomli.load(f)
    except TOMLDecodeError as e:
        raise ConfigError(
            f"Invalid TOML in {path}: {e}",
            config_file=str(path),
        ) from e
    except (OSError, IOError) as e:
        raise ConfigError(
            f"Failed to read config file {path}: {e}",
            config_file=str(path),
        ) from e


def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = base.copy()
    for k, v in override.items():
        if k in result and isinstance(result[k], Dict) and isinstance(v, Dict):
            result[k] = _merge_dicts(result[k], v)
        else:
            result[k] = v
    return result


def load_config(cwd: Optional[Path]) -> Config:
    cwd = cwd or Path.cwd()

    sys_path = get_system_config_path()

    config_dict: Dict[str, Any] = {}

    if sys_path.is_file():
        try:
            config_dict = _parse_toml(sys_path)
        except ConfigError:
            logger.warning(f"Skipping invalid system config: {sys_path}")
        # ~/.config/orion/config.toml

    project_path = _get_project_config(cwd)
    if project_path:
        try:
            project_config_dict = _parse_toml(project_path)
            config_dict = _merge_dicts(config_dict, project_config_dict)
        except ConfigError:
            logger.warning(f"Skipping invalid system config: {sys_path}")
    # C:/coding/personal/projects/orion/config.toml

    if "cwd" not in config_dict:
        config_dict["cwd"] = cwd

    # load dev instructions
    if "developer_instructions" not in config_dict:
        agent_md_content = _get_agent_md_files(cwd)
        if agent_md_content:
            config_dict["developer_instructions"] = agent_md_content

    try:
        config = Config(**config_dict)
    except Exception as e:
        raise ConfigError(f"Invalid configuration: {e}") from e
    return config
