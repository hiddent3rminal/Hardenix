# importing libraries
from modules import ssh
from modules import ufw
from modules import fail2ban
from modules import network
from core import logger
from core import backup
from core import status

# main fucntion to run the sorted modules step by step 

def quick_basic_hardening():

    print("Starting Quick Basic Hardening ...")
    logger.logger.debug("Quick Basic Hardening Started!")
    
    backup.create_backup()
    
    network.configure()

    ssh.configure()

    fail2ban.configure()

    ufw.configure()
  
    status.show_summary()

