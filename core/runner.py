from core import logger
import subprocess


def run_command(command):

    try:


        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )

        logger.logger.debug(f"Command executed successfully: {' '.join(command)}")

        return result

    except PermissionError:
        logger.logger.exception(f"Permission denied while executing command: {' '.join(command)}")
        return None

    except subprocess.CalledProcessError:
        logger.logger.exception(f"Command failed: {' '.join(command)}")
        return None

    except FileNotFoundError:
        logger.logger.exception(f"Command not found: {command[0]}")
        return None

    except Exception:
        logger.logger.exception(f"Unexpected error while executing command: {' '.join(command)}")
        return None


def apply_sysctl(config):

    try:

        logger.logger.info(f"Writing sysctl configuration to {config['file']}")

        with open(config["file"], "w") as file:

            file.write("# Hardenix Network Hardening\n\n")

            for key, value in config["settings"].items():

                logger.logger.debug(f"Setting {key} = {value}")

                file.write(f"{key} = {value}\n")

        if run_command(["sysctl", "--system"]) is None:
            return False

        logger.logger.info("Network hardening applied successfully.")

        return True

    except PermissionError:
        logger.logger.exception("Root privileges are required to write the sysctl configuration.")
        return False

    except KeyError as e:
        logger.logger.exception(f"Missing configuration key: {e}")
        return False

    except Exception:
        logger.logger.exception("Failed to apply network hardening.")
        return False