import os
from core import logger

# UFW configuration path that should be backed up when present.
CONFIG_PATHS = [
    "/etc/ufw"
]

NAME = "ufw"

VERSION = "1.0"

DESCRIPTION = "ufw configuration module"

SUPPORTED_DISTROS = [
    "ubuntu",
    "debian"
]

SERVICES = []

PACKAGES = []



def check_existence():

    # Check whether the UFW configuration directory exists before attempting a backup.
    for path in CONFIG_PATHS:
        if os.path.exists(path):
            logger.logger.info("configuration file Exist!")
            return True
        else:
            logger.logger.warning(f"configuration file could not found! {CONFIG_PATHS}")
    return False



def install():
    pass



def configure():
    pass



def backup():

    # Return the configured path that the backup engine should copy.
    return CONFIG_PATHS



def restore():
    pass



def status():
    pass