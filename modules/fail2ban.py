import os
from core import logger

NAME = "fail2ban"
VERSION = "1.0"

DESCRIPTION = "Avoid of SSH attacks ex: Bruteforce"


SUPPORTED_DISTROS = [
    "ubuntu",
    "debian"
]

CONFIG_PATHS = [
    "/etc/fail2ban"
]

SERVICES = []

PACKAGES = []


def check_existence():

    for path in CONFIG_PATHS:
        if os.path.exists(path):
            logger.logger.info("configuration file exist!")
            return True
        else :
            logger.logger.warning(f"configuration file could not found {CONFIG_PATHS}")
    return False



def install():
    # TODO: Implement distro-aware installation and verify the service is available.
    logger.logger.error("Fail2Ban installation is not implemented.")
    return False



def configure():
    # TODO: Add a jail configuration, validate it, and enable/restart Fail2Ban safely.
    logger.logger.error("Fail2Ban configuration is not implemented; no settings were changed.")
    return False



def backup():

    return CONFIG_PATHS



def restore():
    # TODO: Restore a selected backup only after validating its paths and contents.
    logger.logger.error("Fail2Ban configuration restore is not implemented.")
    return False



def status():
    # TODO: Report Fail2Ban service health and active jails.
    logger.logger.error("Fail2Ban status reporting is not implemented.")
    return False