import os
import shutil
from datetime import datetime

from modules import apache
from modules import bind9
from modules import mysql
from modules import network
from modules import samba
from modules import ntp
from modules import openvpn
from modules import ufw
from modules import ssh


# Backup location
BACKUP_ROOT = "Hardenix_Backup"


SERVICES = [
    ssh,
    apache,
    bind9,
    mysql,
    network,
    samba,
    ntp,
    openvpn,
    ufw
]


def create_backup_folder():

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    backup_dir = os.path.join(
        BACKUP_ROOT,
        timestamp
    )

    os.makedirs(
        backup_dir,
        exist_ok=True
    )

    return backup_dir



def copy_config(source, destination):

    if not os.path.exists(source):
#        print(f"[!] Not found: {source}")
        return False


    try:

        if os.path.isdir(source):

            shutil.copytree(
                source,
                destination,
                dirs_exist_ok=True
            )


        elif os.path.isfile(source):

            shutil.copy2(
                source,
                destination
            )


#        print(f"[+] Copied: {source}")

        return True


    except PermissionError:

#        print(f"[!] Permission denied: {source}")
        return False


    except Exception as e:

        print(
#            f"[!] Error copying {source}: {e}"
        )

        return False



def create_backup():


    backup_dir = create_backup_folder()


    print("\nStarting Hardenix Backup\n")


    for service in SERVICES:


        service_name = service.__name__.split(".")[-1]


#        print(
#            f"\n[*] Checking {service_name}"
#       )


        if service.check_existence():


            service_backup_dir = os.path.join(
                backup_dir,
                service_name
            )


            os.makedirs(
                service_backup_dir,
                exist_ok=True
            )


            paths = service.backup()


            for path in paths:


                destination = os.path.join(
                    service_backup_dir,
                    os.path.basename(path)
                )


                copy_config(
                    path,
                    destination
                )


        # else:

        #     print(
        #         f"[-] {service_name} not found"
        #     )


    print(
        "\nBackup Finished:"
    )

    print(
        backup_dir
    )


    return backup_dir




def compress_folder(folder):


    archive = shutil.make_archive(
        folder,
        "zip",
        folder
    )


    # print(
    #     f"Compressed: {archive}"
    # )

    return archive




def create_metadata():

    pass



if __name__ == "__main__":

    backup_path = create_backup()

    compress_folder(
        backup_path
    )