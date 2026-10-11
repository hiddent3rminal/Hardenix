import os
from core import logger

# SSH configuration directory that should be included in backups.
CONFIG_PATHS = [

    "/etc/ssh"

]

NAME = "SSH"

VERSION = "1.0"

DESCRIPTION = "SSH Hardening Module"

SUPPORTED_DISTROS = [
    "ubuntu",
    "debian"
]

SERVICES = []

PACKAGES = []


def check_existence():

    # Check whether the SSH configuration directory exists before attempting a backup.
    for path in CONFIG_PATHS:

        if os.path.exists(path):
            logger.logger.info("configuration file Exist!")
            return True
        else:
            logger.logger.warning(f"configuration file could not found! {CONFIG_PATHS}")
    return False



def install():
    logger.logger.error("SSH installation is not implemented.")
    return False



def configure():
    logger.logger.error("SSH hardening is not implemented; no SSH settings were changed.")
    return False



def backup():

    # Return the configured path that the backup engine should copy.
    return CONFIG_PATHS



def restore():
    logger.logger.error("SSH configuration restore is not implemented.")
    return False



def status():
    logger.logger.error("SSH status reporting is not implemented.")
    return False