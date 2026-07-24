import os
from core import logger
from core import runner

# Network-related configuration files that should be considered for backup or hardening.
CONFIG_PATHS = [

    "/etc/netplan",

    "/etc/resolv.conf",

    "/etc/hosts",

    "/etc/hostname"

]

# Default sysctl values used by the hardening configuration.
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

    # Return True if at least one expected network config path exists.
    # This helps the backup engine decide whether the service has anything to back up.
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

    # Build the configuration payload for sysctl hardening and hand it to the runner.
    config = {
        "file": "/etc/sysctl.d/99-hardenix.conf",
        "settings": SYSCTL_SETTINGS
    }
    runner.apply_sysctl(config)


def backup():

    # Return the list of paths that should be copied into the backup archive.
    return CONFIG_PATHS



def restore():

    pass



def status():

    runner.run_command("ping -c 4 google.com")