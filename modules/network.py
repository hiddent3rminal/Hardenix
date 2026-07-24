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
            logger.logger.info(f"{path} found.")
            found = True
        else:
            logger.logger.warning(f"{path} not found.")

    return found



def install():

    pass



def configure():

    logger.logger.info("network configuration started!")

    configure_hostname()

    configure_dns()

    configure_ip_static()

    kernel_parameters()

    status()

def backup():

    # Return the list of paths that should be copied into the backup archive.
    return CONFIG_PATHS



def restore():

    pass



def status():

    runner.run_command(["ping", "-c", "4", "google.com"])


def configure_hostname():

    logger.logger.info("hostname configuration started")

    result = runner.run_command(["hostname"])

    if result is None:
        logger.logger.error("Failed to read current hostname!")
        return False

    current_hostname = result.stdout.strip()

    

    get_new_hostname = str(input(f"Your Current Hostname Is : {current_hostname}⚠️\n\/for chnage enter y or Y for keep it press Enter")).strip().lower()


    if get_new_hostname.lower() == "y":
        new_hostname = input("New hostname: ").strip()

        if not new_hostname:
            print("Hostname cannot be empty!")
            return False

        if new_hostname == current_hostname:
            print("hostname is already set.")
            return True

        logger.logger.info(f"hostname from {current_hostname} to {new_hostname}")
        result2 =runner.run_command(["hostnamectl", "set-hostname", new_hostname])

        if result2 is None:
            logger.logger.error("Failed to change hostname.")
            return False

        logger.logger.info(f"hostname changed to {new_hostname}")

        logger.logger.info("editing /etc/hosts")
        with open("/etc/hosts", "r") as file:
            lines = file.readlines()

        found = False
        with open("/etc/hosts", "w") as file:
            for line in lines:
                if line.startswith("127.0.1.1"):
                    file.write(f"127.0.1.1\t{new_hostname}\n")
                    found = True
                else:
                    file.write(line)
            if not found:
                file.write(f"\n127.0.1.1\t{new_hostname}\n")

        return True

    else :
        logger.logger.info("keeping current hostname.")
        return True

def configure_dns():
    pass

def configure_ip_static():
    pass

def kernel_parameters():


    # Build the configuration payload for sysctl hardening and hand it to the runner.
    config = {
        "file": "/etc/sysctl.d/99-hardenix.conf",
        "settings": SYSCTL_SETTINGS
    }
    runner.apply_sysctl(config)




