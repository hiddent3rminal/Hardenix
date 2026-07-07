import os


CONFIG_PATHS = [
    "/etc/openvpn"
]


def check_existence():

    for path in CONFIG_PATHS:
        if os.path.exists(path):
            return True

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