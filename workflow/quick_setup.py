from modules import ssh
from modules import ufw
from modules import fail2ban
from modules import timezone
from modules import network
from core.logger import logger
import time
from core import backup
from core import status

def quick_basic_hardening():

    print("Starting Quick Basic Hardening ...")
    logger.info("Quick Basic Hardening Started!")
    
    backup.create_backup()
    
    network.configure()

    ssh.configure()

    fail2ban.configure()

    ufw.configure()
  
    status.show_summary()