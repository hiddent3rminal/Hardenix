from core import logger


def restore_backup(backup_path: str) -> bool:
    logger.logger.error(
        "Restore is not implemented; backup %s was not applied.",
        backup_path,
    )
    return False