# importing libraries

from core import ascii_art
from workflow import quick_setup
from core import logger 
import os 
import sys

# fucntion to keep the screen clean
def clear_screen():
    command = "cls" if os.name == "nt" else "clear"
    os.system(command)






# function to check the app started as a root or not 
def check_privilege():


    if os.getuid() != 0 :
        print("❌ Hardenix Must Be Run As Root (sudo).\n\n➡️ Try: sudo python3 main.py")
        logger.logger.critical("The Hardenix Did Not Start with Root.")
        return False


    logger.logger.info("hardenix started as a root.")
    return True




# function to checkuser operating system 
def detect_os():

    os_release = "/etc/os-release"
    info = {}

# checking os nfo file existence 
    if not os.path.exists(os_release):
        logger.logger.warning(f"Hardenix Could not find the {os_release} file to detect OS")
        return {
            "id": "unknown",
            "family": "unknown",
            "name": "unknown"
        }

    with open(os_release, "r") as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                info[key] = value.strip('"')

# classyfying os family 
    os_id = info.get("ID", "unknown")
    os_like = info.get("ID_LIKE", "unknown")
    name = info.get("PRETTY_NAME", "Unknown OS")

    if os_id in ("ubuntu", "debian") or "debian" in os_like:
        family = "debian"
    elif os_id in ("rhel", "centos", "fedora") or "rhel" in os_like:
        family = "rhel"
    elif os_id == "arch":
        family = "arch"
    else:
        family = "unknown"

    print(ascii_art)
    print(f"Hardenix initialized on {name} ({family} family) ✅")
    logger.logger.debug(f"user os and version detected succesfully {name} : {family}")

# moving to main menu function     
    logger.logger.info("OS detection was done and move on to main menu")

    return {
        "id": os_id,
        "family": family,
        "name": name
    }




def main_menu(system):
    while True:
        print("What Do You Want ⁉️ (Just Choose number!)⤵️\n\n\n")
        print("1️⃣ ) Quick Basic Hardening (Recommended)")
        print("2️⃣ ) Hardening A Installed Service")
        print("3️⃣ ) Install A Specific Service")
        print("4️⃣ ) Backup / Restore Configuration")
        print("5️⃣ ) System Status Summary")
        print("6️⃣ ) Check New Module Structure")
        print("7️⃣ ) Exit")

        choice = input("Select An Option (1-7): ").strip()


        if not choice.isdigit():
            print("❌ Please enter a valid number!\n")
            logger.logger.warning("User Selected Invalid menu")
            continue



        choice = int(choice)

        if choice < 1 or choice > 7:
            print("❌ Out of range: Choose between 1-7\n")
            continue

# ---- Actions ----


        if choice == 1:
    
            quick_setup.quick_basic_hardening()
            logger.logger.debug("User selected 'quick basic hardening method and specific file parsed! ' ")
        
        elif choice == 2:
            print('do')

            clear_screen()
        
        elif choice == 3:
            print('se')

            clear_screen()
        
        elif choice == 4:
            print('chahar')

            clear_screen()
        
        elif choice == 5:
            print('panj')

            clear_screen()

        elif choice == 6:
            print('shish')

            clear_screen()

        elif choice == 7:
            logger.logger.info("Hardenix Stopped")
            clear_screen()
            sys.exit(0)







if __name__  ==  "__main__":

    logger.logger.info("Hardenix Started!")

    if check_privilege():

        system = detect_os()
        main_menu(system)

