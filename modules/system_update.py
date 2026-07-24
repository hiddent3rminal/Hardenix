import os
from core import logger
from core import runner


def check_update():

    pass


def update():

    runner.run_command("sudo apt update && apt upgrade -y")



def upgrade():
    pass

