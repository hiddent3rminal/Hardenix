from pathlib import Path
import re
import shutil

from core import config, logger, runner


NAME = "SSH"
VERSION = "1.1.0"
DESCRIPTION = "Review and apply guarded OpenSSH server hardening settings"
SUPPORTED_DISTROS = ["ubuntu", "debian"]
CONFIG_PATHS = ["/etc/ssh"]
SERVICES = ["ssh", "sshd"]
PACKAGES = ["openssh-server"]
CONFIG_FILE = Path("/etc/ssh/sshd_config")
DROP_IN = Path("/etc/ssh/sshd_config.d/99-hardenix.conf")
SETTING_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9]*)\s+(\S+)", re.MULTILINE)


def check_existence() -> bool:
    return CONFIG_FILE.is_file() and shutil.which("sshd") is not None


def install() -> bool:
    if shutil.which("apt-get") is None:
        logger.logger.error("SSH installation requires apt-get.")
        return False
    if input("Install OpenSSH server? (y/N): ").strip().lower() != "y":
        logger.logger.info("OpenSSH server installation cancelled.")
        return True
    return runner.run_command(
        ["apt-get", "install", "-y", "openssh-server"],
        timeout=1800,
    ) is not None


def _effective_settings() -> dict[str, str] | None:
    result = runner.run_command(["sshd", "-T"])
    if result is None:
        return None
    return {
        key.lower(): value.lower()
        for key, value in SETTING_RE.findall(result.stdout)
    }


def _reload_service() -> bool:
    for service in SERVICES:
        active = runner.run_command(["systemctl", "is-active", service])
        if active is not None and active.stdout.strip() == "active":
            return runner.run_command(["systemctl", "reload", service]) is not None
    logger.logger.error("Could not find an active SSH service to reload.")
    return False


def configure() -> bool:
    if not check_existence():
        logger.logger.error("OpenSSH server is not installed; no changes were made.")
        return False

    sshd_config = CONFIG_FILE.read_text(encoding="utf-8")
    if not re.search(
        r"^\s*Include\s+/etc/ssh/sshd_config\.d/\*\.conf\s*(?:#.*)?$",
        sshd_config,
        re.IGNORECASE | re.MULTILINE,
    ):
        logger.logger.error(
            "The main sshd_config does not include the Hardenix drop-in directory."
        )
        return False

    current = _effective_settings()
    if current is None:
        return False

    current_root = current.get("permitrootlogin", "prohibit-password")
    current_password = current.get("passwordauthentication", "yes")
    current_max_tries = current.get("maxauthtries", "6")
    print(
        "Current effective SSH settings:\n"
        f"  PermitRootLogin: {current_root}\n"
        f"  PasswordAuthentication: {current_password}\n"
        f"  MaxAuthTries: {current_max_tries}"
    )

    root_choice = input(
        "Permit root login [no/prohibit-password/yes] "
        f"(Enter keeps {current_root}): "
    ).strip().lower()
    if root_choice and root_choice not in {"no", "prohibit-password", "yes"}:
        logger.logger.error("Invalid PermitRootLogin value.")
        return False

    password_choice = input(
        "Password authentication [no/yes] "
        f"(Enter keeps {current_password}): "
    ).strip().lower()
    if password_choice and password_choice not in {"no", "yes"}:
        logger.logger.error("Invalid PasswordAuthentication value.")
        return False
    if password_choice == "no":
        print(
            "Disabling password login can lock out accounts without working SSH keys. "
            "Confirm console or alternate access before continuing."
        )
        if input("Type DISABLE PASSWORD LOGIN to continue: ").strip() != "DISABLE PASSWORD LOGIN":
            logger.logger.info("Password authentication setting was not changed.")
            return False

    max_tries = input(
        "Maximum SSH authentication attempts [3-10] (Enter keeps current): "
    ).strip()
    if max_tries and (
        not max_tries.isdecimal() or not 3 <= int(max_tries) <= 10
    ):
        logger.logger.error("MaxAuthTries must be an integer from 3 to 10.")
        return False

    settings = {}
    if root_choice and root_choice != current_root:
        settings["PermitRootLogin"] = root_choice
    if password_choice and password_choice != current_password:
        settings["PasswordAuthentication"] = password_choice
    if max_tries and max_tries != current_max_tries:
        settings["MaxAuthTries"] = max_tries
    if not settings:
        logger.logger.info("SSH settings are unchanged.")
        return True

    print("The SSH service will be validated and reloaded after saving the settings.")
    if input("Apply these SSH settings? (y/N): ").strip().lower() != "y":
        logger.logger.info("SSH configuration cancelled.")
        return True

    existed = DROP_IN.exists()
    original = DROP_IN.read_bytes() if existed else None
    contents = "# Managed by Hardenix; local changes will be replaced.\n" + "".join(
        f"{key} {value}\n" for key, value in settings.items()
    )
    try:
        config.atomic_write_text(DROP_IN, contents)
    except OSError:
        logger.logger.exception("Could not write SSH settings.")
        return False

    valid = runner.run_command(["sshd", "-t"]) is not None
    effective = _effective_settings() if valid else None
    applied = effective is not None and all(
        effective.get(key.lower()) == value.lower()
        for key, value in settings.items()
    )
    if not valid or not applied or not _reload_service():
        if valid and not applied:
            logger.logger.error(
                "The sshd drop-in was not effective; another SSH setting may override it."
            )
        try:
            if existed and original is not None:
                config.atomic_write_bytes(DROP_IN, original)
            else:
                DROP_IN.unlink(missing_ok=True)
            if runner.run_command(["sshd", "-t"]) is None:
                logger.logger.critical("The previous SSH configuration is invalid after rollback.")
            elif not _reload_service():
                logger.logger.critical("Could not reload SSH after restoring its previous configuration.")
        except OSError:
            logger.logger.exception("Could not restore the previous SSH configuration.")
            logger.logger.critical("SSH may still be using the failed Hardenix configuration.")
        return False
    logger.logger.info("SSH settings were validated and applied.")
    return True


def backup() -> list[str]:
    return CONFIG_PATHS


def status() -> bool:
    if not check_existence():
        print("SSH server: not installed")
        return True
    settings = _effective_settings()
    if settings is None:
        print("SSH configuration: unavailable")
        return False
    service_state = "inactive"
    for service in SERVICES:
        result = runner.run_command(["systemctl", "is-active", service])
        if result is not None and result.stdout.strip() == "active":
            service_state = "active"
            break
    print(
        "SSH server: installed\n"
        f"SSH service: {service_state}\n"
        f"PermitRootLogin: {settings.get('permitrootlogin', 'unknown')}\n"
        "PasswordAuthentication: "
        f"{settings.get('passwordauthentication', 'unknown')}\n"
        f"MaxAuthTries: {settings.get('maxauthtries', 'unknown')}"
    )
    return True
