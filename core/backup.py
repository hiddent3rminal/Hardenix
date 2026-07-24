# Backup engine for collecting configuration files from security-related modules.
# Each service module exposes a simple interface: existence check, backup paths, and optional restore/status behavior.

import os
import shutil
from datetime import datetime
from core import logger
from modules import network
from modules import ufw
from modules import ssh


# Root directory where all timestamped backup folders will be created.
BACKUP_ROOT = "Hardenix_Backup"


# List of service modules that should be included in the backup process.
SERVICES = [
    ssh,
    network,
    ufw
]


def create_backup_folder():

    # Create a unique backup folder name using the current timestamp.
    # This avoids overwriting older backups and makes each run easy to identify.
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    backup_dir = os.path.join(
        BACKUP_ROOT,
        timestamp
    )

    os.makedirs(
        backup_dir,
        exist_ok=True
    )

    logger.logger.info(f"Backup folder created successfully named {backup_dir}")

    return backup_dir



def copy_config(source, destination):

    # Copy a single file or an entire directory into the backup destination.
    # The destination is usually a service-specific folder inside the timestamped backup root.
    if not os.path.exists(source):
        logger.logger.warning(f"config file path could not found or does not exist {source}")

        return False


    try:

        if os.path.isdir(source):

            shutil.copytree(
                source,
                destination,
                dirs_exist_ok=True
            )

            logger.logger.info("Config files copied to Backup folder succefully")

        elif os.path.isfile(source):

            shutil.copy2(
                source,
                destination
            )



            logger.logger.info(f"{source} configuration file copied!")

        return True


    except PermissionError:
        logger.logger.error("Hardenix Doesnt have enough permission to access configuration file")
        return False


    except Exception as e:
        logger.logger.exception("Copying Failed!")
        print(
            f"[!] Error copying {source}: {e}"
        )

        return False



def create_backup():

    # Create the main backup directory first, then process every registered service.
    backup_dir = create_backup_folder()


    print("\nStarting Hardenix Backup\n")  
    logger.logger.info("Backup Started!")


    for service in SERVICES:

        # Use the module name as the folder name inside the backup root.
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

            try :
                paths = service.backup() or []

            except Exception:
                logger.logger.exception(f"{service_name} backup failed")
                continue


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
    logger.logger.info("Back Up Done Succesfully")

    print(
        backup_dir
    )


    return backup_dir




def compress_folder(folder):

    # Create a zip archive of the completed backup folder for easier storage or transfer.
    archive = shutil.make_archive(
        folder,
        "zip",
        folder
    )


    # print(
    #     f"Compressed: {archive}"
    # )
    logger.logger.info("Backup folder successfully compressed")

    return archive




def create_metadata():

    # Placeholder for future metadata creation such as backup ID, timestamp summary, or manifest details.
    pass



if __name__ == "__main__":

    # Run the backup workflow when this script is executed directly.
    backup_path = create_backup()

    compress_folder(
        backup_path
    )