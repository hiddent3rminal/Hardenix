"""Small example module; copy and customize it before registry activation."""

from pathlib import Path

from core import logger


NAME = "Example config"
VERSION = "1.0.0"
DESCRIPTION = "Demonstrates a read-only status and backup module"
SUPPORTED_DISTROS = ["ubuntu", "debian"]
PACKAGES: list[str] = []
SERVICES: list[str] = []
CONFIG_PATHS = ["/etc/example/example.conf"]


def check_existence() -> bool:
    return any(Path(path).exists() for path in CONFIG_PATHS)


def install() -> bool:
    logger.logger.info("This example module does not install software.")
    return True


def configure() -> bool:
    logger.logger.warning("Example module does not make system changes.")
    return False


def backup() -> list[str]:
    return [path for path in CONFIG_PATHS if Path(path).exists()]


def status() -> bool:
    print(f"{NAME}: {'present' if check_existence() else 'not installed'}")
    return True