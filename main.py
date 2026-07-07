# IMPORTING LIBRARIES

from workflow.quick_setup import quick_basic_hardening
import os 
import sys
import time

# Clean Screen After Done
def clear_screen():
    os.system("clear")

ascii_art = "\033[38;5;39m" + r"""


 ██╗    ██╗ ███████╗ ██╗       ██████╗  ██████╗  ███╗   ███╗ ███████╗
 ██║    ██║ ██╔════╝ ██║      ██╔════╝ ██╔═══██╗ ████╗ ████║ ██╔════╝
 ██║ █╗ ██║ █████╗   ██║      ██║      ██║   ██║ ██╔████╔██║ █████╗  
 ██║███╗██║ ██╔══╝   ██║      ██║      ██║   ██║ ██║╚██╔╝██║ ██╔══╝  
 ╚███╔███╔╝ ███████╗ ███████╗ ╚██████╗ ╚██████╔╝ ██║ ╚═╝ ██║ ███████╗
  ╚══╝╚══╝  ╚══════╝ ╚══════╝  ╚═════╝  ╚═════╝  ╚═╝     ╚═╝ ╚══════╝

 ████████╗  ██████╗      ██╗  ██╗  █████╗  ██████╗  ██████╗  ███████╗ ███╗   ██╗ ██╗ ██╗  ██╗
 ╚══██╔══╝ ██╔═══██╗     ██║  ██║ ██╔══██╗ ██╔══██╗ ██╔══██╗ ██╔════╝ ████╗  ██║ ██║ ╚██╗██╔╝
    ██║    ██║   ██║     ███████║ ███████║ ██████╔╝ ██║  ██║ █████╗   ██╔██╗ ██║ ██║  ╚███╔╝ 
    ██║    ██║   ██║     ██╔══██║ ██╔══██║ ██╔══██╗ ██║  ██║ ██╔══╝   ██║╚██╗██║ ██║  ██╔██╗ 
    ██║    ╚██████╔╝     ██║  ██║ ██║  ██║ ██║  ██║ ██████╔╝ ███████╗ ██║ ╚████║ ██║ ██╔╝ ██╗
    ╚═╝     ╚═════╝      ╚═╝  ╚═╝ ╚═╝  ╚═╝ ╚═╝  ╚═╝ ╚═════╝  ╚══════╝ ╚═╝  ╚═══╝ ╚═╝ ╚═╝  ╚═╝


""" + "\033[0m"


# FUNCTION TO CHECK PRIVILAGE
def CheckPrivilage():
    if os.getuid() != 0 :
        print("❌ Hardenix Must Be Run As Root (sudo).\n\n➡️ Try: sudo python3 main.py")
        sys.exit(1)
    else :
        DetectOS()


# FUNCTION TO CHECK OS
def DetectOS():
    os_release = "/etc/os-release"
    info = {}

    # Read OS info
    if not os.path.exists(os_release):
        print("❌ Cannot detect OS: /etc/os-release not found.")
        return

    with open(os_release, "r") as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                info[key] = value.strip('"')

    # classify OS family
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
# moving to main menu function     
    MainMenu()



def MainMenu():
    while True:
        print("What Do You Want ⁉️ (Just Choose number!)⤵️\n\n\n")
        print("1️⃣ ) Quick Basic Hardening (Recommended)")
        print("2️⃣ ) Hardening A Installed Service")
        print("3️⃣ ) Install A Specific Service")
        print("4️⃣ ) Backup / Restore Configuration")
        print("5️⃣ ) System Status Summary")
        print("6️⃣ ) Exit")

        choice = input("Select An Option (1-6): ").strip()


        if not choice.isdigit():
            print("❌ Please enter a valid number!\n")
            continue

        choice = int(choice)

        if choice < 0 or choice > 6:
            print("❌ Out of range: Choose between 1-6\n")
            continue

# ---- Actions ----


        if choice == 1:
            quick_basic_hardening()
            
        elif choice == 2:
            print('do')
            time.sleep(3)
            clear_screen()
        elif choice == 3:
            print('se')
            time.sleep(3)
            clear_screen()
        elif choice == 4:
            print('chahar')
            time.sleep(3)
            clear_screen()
        elif choice == 5:
            print('panj')
            time.sleep(3)
            clear_screen()
        elif choice == 6:
            print("Exiting ...")
            time.sleep(3)
            clear_screen()
            break









CheckPrivilage()













CheckPrivilage()