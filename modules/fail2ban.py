from pathlib import Path
import shutil

from core import config, logger, runner


NAME = "Fail2Ban"
VERSION = "1.1.0"
DESCRIPTION = "Install and configure an SSH brute-force protection jail"
SUPPORTED_DISTROS = ["ubuntu", "debian"]
CONFIG_PATHS = ["/etc/fail2ban"]
SERVICES = ["fail2ban"]
PACKAGES = ["fail2ban"]
JAIL_FILE = Path("/etc/fail2ban/jail.d/99-hardenix.local")
JAIL_CONFIG = (
    "# Managed by Hardenix.\n"
    "[sshd]\n"
    "enabled = true\n"
    "backend = auto\n"
    "maxretry = 5\n"
    "findtime = 10m\n"
    "bantime = 1h\n"
)


def check_existence() -> bool:
    return Path("/etc/fail2ban").is_dir() and shutil.which("fail2ban-client") is not None


def install() -> bool:
    if shutil.which("apt-get") is None:
        logger.logger.error("Fail2Ban installation requires apt-get.")
        return False
    if input("Install Fail2Ban? (y/N): ").strip().lower() != "y":
        logger.logger.info("Fail2Ban installation cancelled.")
        return True
    return runner.run_command(
        ["apt-get", "install", "-y", "fail2ban"],
        timeout=1800,
    ) is not None


def configure() -> bool:
    if not check_existence():
        logger.logger.error("Fail2Ban is not installed; no changes were made.")
        return False

    existed = JAIL_FILE.exists()
    if input(
        "Enable a 5-attempt, 10-minute SSH jail with a 1-hour ban? "
        "This replaces the Hardenix-managed jail file. (y/N): "
    ).strip().lower() != "y":
        logger.logger.info("Fail2Ban configuration cancelled.")
        return True
    original = JAIL_FILE.read_bytes() if existed else None
    try:
        config.atomic_write_text(JAIL_FILE, JAIL_CONFIG)
    except OSError:
        logger.logger.exception("Could not write Fail2Ban configuration.")
        return False

    if runner.run_command(["fail2ban-client", "-t"]) is None:
        _restore_jail(original, existed)
        return False

    if runner.run_command(["systemctl", "enable", "--now", "fail2ban"]) is None:
        if _restore_jail(original, existed):
            if runner.run_command(["systemctl", "restart", "fail2ban"]) is None:
                logger.logger.critical(
                    "Could not restart Fail2Ban after restoring its previous configuration."
                )
        return False

    if runner.run_command(["fail2ban-client", "status", "sshd"]) is None:
        logger.logger.error("Fail2Ban started, but the SSH jail is not active.")
        if _restore_jail(original, existed):
            if runner.run_command(["systemctl", "restart", "fail2ban"]) is None:
                logger.logger.critical(
                    "Could not restart Fail2Ban after restoring its previous configuration."
                )
        return False
    logger.logger.info("Fail2Ban SSH jail enabled.")
    return True


def _restore_jail(original: bytes | None, existed: bool) -> bool:
    try:
        if existed and original is not None:
            config.atomic_write_bytes(JAIL_FILE, original)
        else:
            JAIL_FILE.unlink(missing_ok=True)
    except OSError:
        logger.logger.exception("Could not restore previous Fail2Ban configuration.")
        logger.logger.critical("Fail2Ban may still be using the failed Hardenix configuration.")
        return False
    return True


def backup() -> list[str]:
    return CONFIG_PATHS


def status() -> bool:
    if not check_existence():
        print("Fail2Ban: not installed")
        return True
    result = runner.run_command(["fail2ban-client", "status"])
    if result is None:
        print("Fail2Ban status: unavailable")
        return False
    print(f"Fail2Ban status:\n{result.stdout.strip()}")
    return True
