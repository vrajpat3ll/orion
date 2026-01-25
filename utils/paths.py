from pathlib import Path
from typing import Union


def resolve_path(base: Union[str, Path], path: Union[str, Path]) -> Path:
    path = Path(path)
    if path.absolute():
        return path.resolve()
    return Path(base).resolve() / path


def display_path_rel_to_cwd(path: str, cwd: Union[Path, None] = None) -> str:
    try:
        p = Path(path)
    except Exception:
        return path

    if cwd:
        try:
            return str(p.relative_to(cwd))
        except ValueError:
            pass

    return str(p)


def ensure_parent_directory(path: Union[Path, str]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def is_binary_path(path: Union[str, Path]) -> bool:
    try:
        with open(path, "rb") as f:
            chunk = f.read(8 * (1 << 10))
            return b"\x00" in chunk
    except (OSError, IOError):
        return False
