import logging
from pathlib import Path


logger = logging.getLogger("Hardenix")
logger.setLevel(logging.DEBUG)
logger.propagate = False

if not logger.handlers:
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    log_path = Path(__file__).resolve().parents[1] / "logs" / "hardenix.log"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
    except OSError as error:
        logger.warning("File logging unavailable at %s: %s", log_path, error)
    else:
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
