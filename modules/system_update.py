import re

from core import logger, runner


NAME = "system packages"
VERSION = "1.0"
DESCRIPTION = "System update and package management module"
SUPPORTED_DISTROS = ["ubuntu", "debian"]
CONFIG_PATHS = []
SERVICES = []
PACKAGES = []


def check_update() -> int | None:
    result = runner.run_command(["apt-get", "-s", "upgrade"])
    if result is None:
        return None
    match = re.search(r"^(\d+) upgraded,", result.stdout, re.MULTILINE)
    if match is None:
        logger.logger.error("Could not parse apt-get's simulated upgrade result.")
        return None
    return int(match.group(1))


def update() -> bool:
    # TODO: Require an explicit operator confirmation before package upgrades.
    if runner.run_command(["apt-get", "update"]) is None:
        logger.logger.error("Package index update failed.")
        return False
    return upgrade()


def upgrade() -> bool:
    if runner.run_command(["apt-get", "upgrade", "-y"]) is None:
        logger.logger.error("Package upgrade failed.")
        return False
    logger.logger.info("System package upgrade completed.")
    return True
