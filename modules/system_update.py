import re
import shutil

from core import logger, runner


NAME = "system packages"
VERSION = "1.0"
DESCRIPTION = "System update and package management module"
SUPPORTED_DISTROS = ["ubuntu", "debian"]
CONFIG_PATHS = []
SERVICES = []
PACKAGES = []


def check_existence() -> bool:
    return shutil.which("apt-get") is not None


def install() -> bool:
    logger.logger.info("System updates are provided by the operating system package manager.")
    return True


def configure() -> bool:
    return update()


def backup() -> list[str]:
    return []


def status() -> bool:
    available = check_update()
    if available is None:
        print("Package updates: unavailable")
        return False
    print(f"Available package upgrades: {available}")
    return True


def check_update() -> int | None:
    result = runner.run_command(
        ["apt-get", "-s", "upgrade"],
        env={"LC_ALL": "C"},
    )
    if result is None:
        return None
    match = re.search(r"^(\d+) upgraded,", result.stdout, re.MULTILINE)
    if match is None:
        logger.logger.error("Could not parse apt-get's simulated upgrade result.")
        return None
    return int(match.group(1))


def update() -> bool:
    if runner.run_command(["apt-get", "update"], timeout=1800) is None:
        logger.logger.error("Package index update failed.")
        return False

    available = check_update()
    if available is None:
        return False
    print(f"Available package upgrades: {available}")
    if available == 0:
        logger.logger.info("No package upgrades are available.")
        return True
    if input(f"Upgrade {available} package(s) now? (y/N): ").strip().lower() != "y":
        logger.logger.info("System package upgrade cancelled.")
        return True
    return _upgrade_packages()


def upgrade() -> bool:
    if input("Run the APT package upgrade now? (y/N): ").strip().lower() != "y":
        logger.logger.info("System package upgrade cancelled.")
        return True
    return _upgrade_packages()


def _upgrade_packages() -> bool:
    if runner.run_command(
        ["apt-get", "upgrade", "-y"],
        timeout=1800,
    ) is None:
        logger.logger.error("Package upgrade failed.")
        return False
    logger.logger.info("System package upgrade completed.")
    return True
