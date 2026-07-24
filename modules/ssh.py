import os
from core import logger

# SSH configuration directory that should be included in backups.
CONFIG_PATHS = [

    "/etc/ssh"

]



def check_existence():

    # Check whether the SSH configuration directory exists before attempting a backup.
    for path in CONFIG_PATHS:

        if os.path.exists(path):
            logger.info("configuration file Exist!")
            return True
        else:
            logger.warning(f"configuration file could not found! {CONFIG_PATHS}")
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