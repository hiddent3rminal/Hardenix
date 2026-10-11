from collections.abc import Sequence
from pathlib import Path
import subprocess

from core import logger


def run_command(command: Sequence[str]) -> subprocess.CompletedProcess[str] | None:
    """Run one command without a shell; return None when it cannot succeed."""
    if isinstance(command, (str, bytes)) or not command:
        raise ValueError("command must be a non-empty sequence of arguments")

    command_args = list(command)
    if any(not isinstance(argument, str) for argument in command_args):
        raise TypeError("all command arguments must be strings")

    try:
        result = subprocess.run(
            command_args,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        logger.logger.error(
            "Command failed (%s): %s",
            error.returncode,
            " ".join(command_args),
        )
        if error.stderr:
            logger.logger.error("%s", error.stderr.strip())
        return None
    except OSError:
        logger.logger.exception("Could not execute command: %s", command_args[0])
        return None

    logger.logger.debug("Command executed successfully: %s", " ".join(command_args))
    return result


def apply_sysctl(config: dict[str, object]) -> bool:
    try:
        config_file = config["file"]
        settings = config["settings"]
        if not isinstance(config_file, str) or not isinstance(settings, dict):
            raise TypeError("sysctl config must contain a string file and settings mapping")

        path = Path(config_file)
        previous_contents = path.read_bytes() if path.exists() else None
        logger.logger.info("Writing sysctl configuration to %s", config_file)
        try:
            with path.open("w", encoding="utf-8") as file:
                file.write("# Hardenix Network Hardening\n\n")
                for key, value in settings.items():
                    file.write(f"{key} = {value}\n")
        except OSError:
            if previous_contents is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(previous_contents)
            raise

        if run_command(["sysctl", "--system"]) is None:
            try:
                if previous_contents is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(previous_contents)
                if run_command(["sysctl", "--system"]) is None:
                    logger.logger.error(
                        "Runtime sysctl settings may not match the restored configuration."
                    )
            except OSError:
                logger.logger.exception("Could not roll back %s.", config_file)
            return False

        logger.logger.info("Network hardening applied successfully.")
        return True
    except (OSError, KeyError, TypeError):
        logger.logger.exception("Failed to apply network hardening.")
        return False
