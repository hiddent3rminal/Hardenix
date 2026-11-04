import json
import os
from pathlib import Path
import shutil
import tempfile

from core import logger
from modules.registry import get_modules


BACKUP_ROOT = Path("/var/backups/hardenix").resolve()


def _safe_destination(source: str) -> Path:
    if not isinstance(source, str):
        raise ValueError("Restore destination must be a string path.")
    destination = Path(source)
    if not destination.is_absolute() or ".." in destination.parts:
        raise ValueError(f"Unsafe restore destination: {source}")
    return destination


def _replace_from_backup(backup_source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if backup_source.is_dir():
        temporary = Path(
            tempfile.mkdtemp(prefix=f".{destination.name}.restore-", dir=destination.parent)
        )
        shutil.rmtree(temporary)
        shutil.copytree(backup_source, temporary, symlinks=True)
        if destination.exists() or destination.is_symlink():
            if destination.is_dir() and not destination.is_symlink():
                shutil.rmtree(destination)
            else:
                destination.unlink()
        os.replace(temporary, destination)
        return

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.restore-",
        dir=destination.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        shutil.copy2(backup_source, temporary, follow_symlinks=False)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def restore_backup(backup_path: str) -> bool:
    path = Path(backup_path).resolve()
    try:
        path.relative_to(BACKUP_ROOT)
    except ValueError:
        logger.logger.error("Backup must be located beneath %s.", BACKUP_ROOT)
        return False
    if not path.is_dir() or path.is_symlink():
        logger.logger.error("Backup path is not a valid directory.")
        return False

    manifest_path = path / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        logger.logger.exception("Could not read the backup manifest.")
        return False
    if not isinstance(manifest, dict) or manifest.get("version") != 1:
        logger.logger.error("Unsupported or invalid backup manifest.")
        return False
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        logger.logger.error("Backup manifest contains no restorable entries.")
        return False

    allowed_destinations = {
        Path(config_path).resolve()
        for module in get_modules()
        for config_path in module.backup()
    }
    validated = []
    try:
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError("Invalid manifest entry.")
            source_name = entry.get("backup")
            source_path = Path(source_name) if isinstance(source_name, str) else Path()
            if (
                source_path.is_absolute()
                or not source_path.parts
                or ".." in source_path.parts
                or source_path.parts[0] == "manifest.json"
            ):
                raise ValueError("Unsafe backup-relative path.")
            source = (path / source_path).resolve()
            source.relative_to(path)
            if not source.exists() or source.is_symlink():
                raise ValueError(f"Backup data is missing or unsafe: {source_path}")
            destination = _safe_destination(entry.get("source", "")).resolve()
            if destination not in allowed_destinations:
                raise ValueError(f"Destination is not registered for restore: {destination}")
            validated.append((source, destination))
        destinations = [destination for _, destination in validated]
        if len(destinations) != len(set(destinations)):
            raise ValueError("Backup manifest contains duplicate destinations.")
    except (TypeError, ValueError, OSError, RuntimeError):
        logger.logger.exception("Backup manifest failed validation.")
        return False

    if input(
        f"Restore {len(validated)} configuration path(s) from {path}? "
        "Current files will be overwritten. Type RESTORE to continue: "
    ).strip() != "RESTORE":
        logger.logger.info("Backup restore cancelled.")
        return True

    rollback_root = Path(tempfile.mkdtemp(prefix="hardenix-restore-rollback-"))
    changed = []
    try:
        for source, destination in validated:
            rollback = rollback_root / str(len(changed))
            existed = destination.exists() or destination.is_symlink()
            if existed:
                if destination.is_dir() and not destination.is_symlink():
                    shutil.copytree(destination, rollback, symlinks=True)
                else:
                    rollback.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(destination, rollback, follow_symlinks=False)
            changed.append((destination, rollback, existed))
            _replace_from_backup(source, destination)
    except (OSError, shutil.Error):
        logger.logger.exception("Restore failed; attempting to roll back changed paths.")
        rollback_ok = True
        for destination, rollback, existed in reversed(changed):
            try:
                if existed:
                    _replace_from_backup(rollback, destination)
                elif destination.is_dir() and not destination.is_symlink():
                    shutil.rmtree(destination)
                else:
                    destination.unlink(missing_ok=True)
            except OSError:
                rollback_ok = False
                logger.logger.exception("Could not roll back %s.", destination)
        if not rollback_ok:
            logger.logger.critical("Restore failed and rollback was incomplete.")
        return False
    finally:
        try:
            shutil.rmtree(rollback_root)
        except OSError:
            logger.logger.exception("Could not remove temporary restore rollback data.")

    logger.logger.info("Restored %s configuration path(s) from %s.", len(validated), path)
    return True
