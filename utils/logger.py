from datetime import datetime
import logging

# from datetime import datetime
from pathlib import Path
import os

# Generate the log file ONCE per run
root_dir = Path(__file__).resolve().parent.parent
log_dir = root_dir / "logs"
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

# Configure the root logger only once
logging.basicConfig(level=logging.INFO)  # basic fallback

# Disable logging from noisy libraries
# logging.getLogger("google_genai.models").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
# logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str, log_level: int = logging.INFO) -> logging.Logger:
    """
    Returns a configured logger instance for the given module name.
    Logs to both console and a single run-specific file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        return logger

    # Formatter
    _old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = _old_factory(*args, **kwargs)
        try:
            record.name = os.path.relpath(record.pathname, start=str(root_dir))
        except Exception:
            record.name = record.pathname
        return record

    logging.setLogRecordFactory(record_factory)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File Handler (same file for the whole run)
    fh = logging.FileHandler(log_file, mode="a")
    fh.setLevel(log_level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Prevent double logging via root logger
    logger.propagate = False

    return logger
