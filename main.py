# importing libraries

from core import banner
from workflow import quick_setup
from core import logger 
from core import backup, status
import os 
import sys

# fucntion to keep the screen clean
def clear_screen():
    print("\033[2J\033[H", end="")






# function to check the app started as a root or not 
def check_privilege():


    if os.getuid() != 0 :
        print("❌ Hardenix must be run as root.\n\n➡️ Try: sudo python3 main.py")
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

    print(banner.ascii_art)
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
        print(f"Detected system: {system['name']} ({system['family']} family)\n")
        print("What Do You Want ⁉️ (Just Choose number!)⤵️\n\n\n")
        print("1️⃣ ) Quick Basic Hardening (partial - review supported features)")
        print("2️⃣ ) Harden an installed service (not implemented)")
        print("3️⃣ ) Install a specific service (not implemented)")
        print("4️⃣ ) Backup / Restore Configuration")
        print("5️⃣ ) System Status Summary")
        print("6️⃣ ) Module structure information")
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
            if not quick_setup.quick_basic_hardening():
                print("❌ Hardening workflow did not complete. Check the log for details.")
            logger.logger.debug("User selected 'quick basic hardening method and specific file parsed! ' ")
        
        elif choice == 2:
            print("Installed-service hardening is not implemented; no changes were made.")
        
        elif choice == 3:
            print("Service installation is not implemented; no changes were made.")
        
        elif choice == 4:
            action = input("1) Create configuration backup\n2) Restore (not implemented)\nSelect: ").strip()
            if action == "1":
                backup_path = backup.create_backup()
                if backup_path is False:
                    print("❌ Backup failed or was incomplete.")
                else:
                    try:
                        archive = backup.compress_folder(backup_path)
                    except OSError:
                        logger.logger.exception("Could not compress the backup.")
                        print("❌ Backup was created but compression failed.")
                    else:
                        print(f"✅ Backup created: {archive}")
            elif action == "2":
                print("Restore is not implemented; no files were changed.")
            else:
                print("Invalid option.")
        
        elif choice == 5:
            if not status.show_summary():
                print("⚠️ Some status checks were unavailable.")

        elif choice == 6:
            print("Modules should expose explicit check, configure, backup, and restore behavior.")
            print("See templates/module_template.py.")

        elif choice == 7:
            logger.logger.info("Hardenix Stopped and Exited")
            clear_screen()
            sys.exit(0)







if __name__  ==  "__main__":

    logger.logger.info("Hardenix Started!")

    if check_privilege():

        system = detect_os()
        main_menu(system)
