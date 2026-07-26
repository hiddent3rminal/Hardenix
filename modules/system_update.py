import os
from core import logger
from core import runner

NAME = "system packages"

VERSION = "1.0"

DESCRIPTION = "system update and packages managment module"

SUPPORTED_DISTROS = [
    "ubuntu",
    "debian"
]

CONFIG_PATHS = []

SERVICES = []

PACKAGES = []


def check_update():

    pass


def update():

    runner.run_command("sudo apt update && apt upgrade -y")



def upgrade():
    pass

