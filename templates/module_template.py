"""Copy this module into modules/ and register it in modules/registry.py.

All module functions execute with the privileges of the Hardenix process.
Validate input, use core.runner.run_command for external commands, and never
load modules from untrusted or user-writable directories.
"""

from pathlib import Path

from core import logger


NAME = "Example service"
VERSION = "1.0.0"
DESCRIPTION = "Describe what this module manages"
SUPPORTED_DISTROS = ["ubuntu", "debian"]
PACKAGES: list[str] = []
SERVICES: list[str] = []
CONFIG_PATHS: list[str] = []


def check_existence() -> bool:
    return False


def install() -> bool:
    logger.logger.error("Implement an explicit, distro-checked installation flow.")
    return False


def configure() -> bool:
    logger.logger.error("Implement validation, backup, apply, and post-change checks.")
    return False


def backup() -> list[str]:
    return [path for path in CONFIG_PATHS if Path(path).exists()]


def status() -> bool:
    print(f"{NAME}: status reporting is not implemented.")
    return False