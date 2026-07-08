from core.logger import logger
import subprocess

def run_command() :
    pass

def apply_sysctl(config):

    try:

        with open(config["file"], "w") as file:

            file.write("# Hardenix Network Hardening\n\n")

            for key, value in config["settings"].items():
                file.write(f"{key} = {value}\n")

        subprocess.run(
            ["sysctl", "--system"],
            check=True
        )

        logger.info("Network hardening applied successfully.")

        return True

    except Exception:
        logger.exception("Failed to apply network hardening.")
        return False
    except PermissionError:
        logger.error("Root privilage are required to apply sysctl config")
        return False