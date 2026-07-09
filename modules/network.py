import os
from core import logger
from core import runner

CONFIG_PATHS = [

    "/etc/netplan",

    "/etc/resolv.conf",

    "/etc/hosts",

    "/etc/hostname"

]

SYSCTL_SETTINGS = {
    "net.ipv4.ip_forward": "0",
    "net.ipv4.conf.all.accept_redirects": "0",
    "net.ipv4.conf.default.accept_redirects": "0",
    "net.ipv4.conf.all.send_redirects": "0",
    "net.ipv4.conf.default.send_redirects": "0",
    "net.ipv4.conf.all.accept_source_route": "0",
    "net.ipv4.conf.default.accept_source_route": "0",
    "net.ipv4.conf.all.rp_filter": "1",
    "net.ipv4.conf.default.rp_filter": "1",
    "net.ipv4.tcp_syncookies": "1"
}



def check_existence():

    found = False

    for path in CONFIG_PATHS:

        if os.path.exists(path):
            logger.info(f"{path} found.")
            found = True
        else:
            logger.warning(f"{path} not found.")

    return found



def install():

    pass



def configure():

    config = {
        "file": "/etc/sysctl.d/99-hardenix.conf",
        "settings": SYSCTL_SETTINGS
    }
    runner.apply_sysctl(config)


def backup():

    return CONFIG_PATHS



def restore():

    pass



def status():

    pass