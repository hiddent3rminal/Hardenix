import os
from core.logger import logger

CONFIG_PATHS = [
    "/etc/openvpn"
]


def check_existence():

    for path in CONFIG_PATHS:
        if os.path.exists(path):
            logger.info("configuration file Exist! ")
            return True
        else: 
            logger.warning(f"configuration file could not found! {CONFIG_PATHS}")
    return False



def install():
    pass



def configure():
    pass



def backup():

    return CONFIG_PATHS



def restore():
    pass



def status():
    pass