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
    logger.logger.error("Fail2Ban installation is not implemented.")
    return False



def configure():
    logger.logger.error("Fail2Ban configuration is not implemented; no settings were changed.")
    return False



def backup():

    return CONFIG_PATHS



def restore():
    logger.logger.error("Fail2Ban configuration restore is not implemented.")
    return False



def status():
    logger.logger.error("Fail2Ban status reporting is not implemented.")
    return False