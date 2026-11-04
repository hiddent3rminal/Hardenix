from collections.abc import Sequence
import os
from pathlib import Path
import subprocess

from core import config as config_writer, logger


def run_command(
    command: Sequence[str],
    *,
    timeout: float = 120,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str] | None:
    """Run one command without a shell; return None when it cannot succeed."""
    if isinstance(command, (str, bytes)) or not command:
        raise ValueError("command must be a non-empty sequence of arguments")

    command_args = list(command)
    if any(not isinstance(argument, str) for argument in command_args):
        raise TypeError("all command arguments must be strings")

    try:
        if env is None:
            result = subprocess.run(
                command_args,
                check=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        else:
            command_env = os.environ.copy()
            command_env.update(env)
            result = subprocess.run(
                command_args,
                check=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=command_env,
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
    except subprocess.TimeoutExpired:
        logger.logger.error("Command timed out: %s", " ".join(command_args))
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
        contents = "# Hardenix Network Hardening\n\n" + "".join(
            f"{key} = {value}\n" for key, value in settings.items()
        )
        config_writer.atomic_write_text(path, contents)

        if run_command(["sysctl", "--system"]) is None:
            try:
                if previous_contents is None:
                    path.unlink(missing_ok=True)
                else:
                    config_writer.atomic_write_bytes(path, previous_contents)
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
