import logging
import os
import sys

# Create logs directory
os.makedirs("logs", exist_ok=True)

# Create logger
logger = logging.getLogger("Hardenix")
logger.setLevel(logging.DEBUG)

# Prevent duplicate handlers
if not logger.handlers:

    # Console output
    # console_handler = logging.StreamHandler(sys.stdout)
    # console_handler.setLevel(logging.INFO)

    # Log file
    file_handler = logging.FileHandler(
        "logs/hardenix.log",
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)

    # Log format
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )

    # console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # logger.addHandler(console_handler)
    logger.addHandler(file_handler)