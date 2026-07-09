from core.logger import logger
import subprocess


def run_command(command):

    try:

        logger.debug(f"Executing command: {' '.join(command)}")

        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )

        logger.debug(f"Command executed successfully: {' '.join(command)}")

        return result

    except PermissionError:
        logger.exception(f"Permission denied while executing command: {' '.join(command)}")
        return None

    except subprocess.CalledProcessError:
        logger.exception(f"Command failed: {' '.join(command)}")
        return None

    except FileNotFoundError:
        logger.exception(f"Command not found: {command[0]}")
        return None

    except Exception:
        logger.exception(f"Unexpected error while executing command: {' '.join(command)}")
        return None


def apply_sysctl(config):

    try:

        logger.info(f"Writing sysctl configuration to {config['file']}")

        with open(config["file"], "w") as file:

            file.write("# Hardenix Network Hardening\n\n")

            for key, value in config["settings"].items():

                logger.debug(f"Setting {key} = {value}")

                file.write(f"{key} = {value}\n")

        if run_command(["sysctl", "--system"]) is None:
            return False

        logger.info("Network hardening applied successfully.")

        return True

    except PermissionError:
        logger.exception("Root privileges are required to write the sysctl configuration.")
        return False

    except KeyError as e:
        logger.exception(f"Missing configuration key: {e}")
        return False

    except Exception:
        logger.exception("Failed to apply network hardening.")
        return False