# Backup engine for collecting configuration files from security-related modules.
# Each service module exposes a simple interface: existence check, backup paths, and optional restore/status behavior.

import os
import shutil
from datetime import datetime
from core import logger
from modules import network
from modules import ssh
from modules import timezone


# Root directory where all timestamped backup folders will be created.
BACKUP_ROOT = "Hardenix_Backup"


# List of service modules that should be included in the backup process.
SERVICES = [
    ssh,
    network,
    timezone,
]


def create_backup_folder():

    # Create a unique backup folder name using the current timestamp.
    # This avoids overwriting older backups and makes each run easy to identify.
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")

    backup_dir = os.path.join(
        BACKUP_ROOT,
        timestamp
    )

    os.makedirs(backup_dir, exist_ok=False)

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
        else:
            logger.logger.error("Unsupported configuration path: %s", source)
            return False
        return True
    except OSError:
        logger.logger.exception("Copying configuration failed: %s", source)
        return False



def create_backup():
    """Back up available configuration and return False if any copy fails."""
    try:
        backup_dir = create_backup_folder()
    except OSError:
        logger.logger.exception("Could not create the backup directory.")
        return False

    print("\nStarting Hardenix Backup\n")
    logger.logger.info("Backup started.")
    copied_count = 0
    failed = False

    for service in SERVICES:
        service_name = service.__name__.split(".")[-1]
        try:
            if not service.check_existence():
                logger.logger.info("No configuration found for %s; skipping.", service_name)
                continue

            paths = service.backup() or []
            if not paths:
                logger.logger.warning("%s returned no backup paths.", service_name)
                continue

            service_backup_dir = os.path.join(backup_dir, service_name)
            os.makedirs(service_backup_dir, exist_ok=True)

            for path in paths:
                if not os.path.exists(path):
                    logger.logger.info("Optional configuration path is absent; skipping: %s", path)
                    continue
                destination = os.path.join(service_backup_dir, os.path.basename(path))
                if copy_config(path, destination):
                    copied_count += 1
                else:
                    failed = True
        except (OSError, AttributeError, TypeError):
            logger.logger.exception("Backup failed for %s.", service_name)
            failed = True

    if failed or copied_count == 0:
        logger.logger.error(
            "Backup incomplete (%s paths copied); it will not be treated as successful.",
            copied_count,
        )
        return False

    print("\nBackup Finished:")
    print(backup_dir)
    logger.logger.info("Backup completed: %s", backup_dir)
    return backup_dir




def compress_folder(folder):

    # Create a zip archive of the completed backup folder for easier storage or transfer.
    archive = shutil.make_archive(folder, "zip", folder)


    # print(
    #     f"Compressed: {archive}"
    # )
    logger.logger.info("Backup folder successfully compressed: %s", archive)

    return archive




if __name__ == "__main__":
    backup_path = create_backup()
    if backup_path is False:
        raise SystemExit("Backup failed.")
    try:
        compress_folder(backup_path)
    except OSError:
        logger.logger.exception("Backup was created but compression failed.")
        raise SystemExit("Could not compress backup.")