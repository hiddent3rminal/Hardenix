from datetime import datetime
import os
from pathlib import Path
import re
import shutil
import time

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

from core import logger, runner


NAME = "timezone"
VERSION = "1.0"
DESCRIPTION = "Date and time setup module"
SUPPORTED_DISTROS = ["ubuntu", "debian"]
TIMESYNCD_CONFIG = "/etc/systemd/timesyncd.conf"
CONFIG_PATHS = [TIMESYNCD_CONFIG]
SERVICES = []
PACKAGES = []


def check_existence() -> bool:
    return os.path.exists(TIMESYNCD_CONFIG)


def install() -> bool:
    logger.logger.warning("Timezone module does not install time-sync packages.")
    return False


def configure() -> bool:
    while True:
        choice = input(
            "\n1) Change timezone\n"
            "2) Set time manually\n"
            "3) Enable/disable NTP\n"
            "4) Change NTP server\n"
            "5) Sync with NTP now\n"
            "Enter) Skip\n"
            "Select: "
        ).strip().lower()

        actions = {
            "1": _change_timezone,
            "2": _change_time_manually,
            "3": _change_ntp_status,
            "4": _change_ntp_server,
            "5": _sync_ntp,
        }
        if choice == "":
            logger.logger.info("Timezone configuration skipped by user.")
            return True
        if choice in actions:
            return actions[choice]()
        print("Invalid option, try again.")


def backup() -> list[str]:
    return CONFIG_PATHS


def restore() -> bool:
    logger.logger.error("Timezone configuration restore is not implemented.")
    return False


def _get_property(name: str) -> str | None:
    result = runner.run_command(["timedatectl", "show", f"--property={name}"])
    if result is None:
        return None
    key, separator, value = result.stdout.partition("=")
    if not separator or key != name:
        logger.logger.error("timedatectl returned an invalid %s property.", name)
        return None
    return value.strip()


def status() -> bool:
    properties = ("Timezone", "TimeUSec", "NTP", "NTPSynchronized")
    values = {name: _get_property(name) for name in properties}
    if any(value is None for value in values.values()):
        logger.logger.error("Could not collect complete time status.")
        return False

    print(
        f"Timezone: {values['Timezone']}\n"
        f"Current time: {values['TimeUSec']}\n"
        f"NTP enabled: {values['NTP']}\n"
        f"NTP synchronized: {values['NTPSynchronized']}"
    )
    return True


def _get_timezones() -> list[str]:
    result = runner.run_command(["timedatectl", "list-timezones"])
    if result is None:
        return []
    return result.stdout.splitlines()


def _select_timezone() -> str | None:
    timezones = _get_timezones()
    if not timezones:
        logger.logger.error("No timezones could be retrieved.")
        return None

    selected = prompt(
        "Select timezone: ",
        completer=WordCompleter(timezones, ignore_case=True),
    ).strip()
    if selected not in timezones:
        logger.logger.error("The selected timezone is not in the system timezone list.")
        return None
    return selected


def _set_timezone(timezone: str) -> bool:
    result = runner.run_command(["timedatectl", "set-timezone", timezone])
    if result is None:
        print("Could not change the timezone.")
        return False
    print(f"Timezone changed to {timezone}.")
    logger.logger.info("Timezone changed to %s.", timezone)
    return True


def _change_timezone() -> bool:
    timezone = _select_timezone()
    return _set_timezone(timezone) if timezone else False


def _validate_datetime(date: str, time_value: str) -> bool:
    try:
        parsed = datetime.strptime(
            f"{date} {time_value}",
            "%Y-%m-%d %H:%M:%S",
        )
    except ValueError:
        return False
    return (
        parsed.strftime("%Y-%m-%d") == date
        and parsed.strftime("%H:%M:%S") == time_value
    )


def _change_time_manually() -> bool:
    while True:
        date = input("Enter date (YYYY-MM-DD): ").strip()
        time_value = input("Enter time (HH:MM:SS): ").strip()
        if _validate_datetime(date, time_value):
            break
        print("Invalid date or time.")

    current_ntp = _get_property("NTP")
    if current_ntp is None or current_ntp.lower() not in {"yes", "no"}:
        logger.logger.error("Could not determine whether NTP is enabled.")
        return False

    if current_ntp.lower() == "yes":
        if runner.run_command(["timedatectl", "set-ntp", "false"]) is None:
            print("Could not disable NTP.")
            return False

    result = runner.run_command(["timedatectl", "set-time", f"{date} {time_value}"])
    if result is None:
        if current_ntp.lower() == "yes":
            if runner.run_command(["timedatectl", "set-ntp", "true"]) is None:
                logger.logger.error("Could not restore the previous NTP-enabled state.")
        print("Failed to change system time.")
        return False

    print("System date/time changed successfully.")
    logger.logger.info("System date/time changed to %s %s.", date, time_value)
    return True


def _change_ntp_status() -> bool:
    ntp_status = _get_property("NTP")
    if ntp_status is None or ntp_status.lower() not in {"yes", "no"}:
        logger.logger.error("Could not determine the current NTP status.")
        return False

    target = "false" if ntp_status.lower() == "yes" else "true"
    answer = input(f"NTP is {ntp_status}. Change it? (y/N): ").strip().lower()
    if answer != "y":
        return True

    result = runner.run_command(["timedatectl", "set-ntp", target])
    if result is None:
        print("Could not change NTP status.")
        return False
    print(f"NTP {'disabled' if target == 'false' else 'enabled'}.")
    return True


def _detect_ntp_service() -> str | None:
    for service in ("systemd-timesyncd", "chrony", "ntp", "ntpd"):
        result = runner.run_command(["systemctl", "is-active", service])
        if result is not None and result.stdout.strip() == "active":
            return service
    return None


def _get_current_ntp_server() -> str | None:
    result = runner.run_command(
        ["timedatectl", "show-timesync", "--property=ServerName"]
    )
    if result is None:
        logger.logger.error("Could not get the current NTP server.")
        return None
    _, separator, server = result.stdout.partition("=")
    return server.strip() if separator else None


def _change_ntp_server() -> bool:
    service = _detect_ntp_service()
    if service != "systemd-timesyncd":
        logger.logger.error("Changing the NTP server is supported only for systemd-timesyncd.")
        print(f"Unsupported NTP service: {service or 'none detected'}.")
        return False

    current = _get_current_ntp_server()
    print(f"Current NTP server: {current or 'Default/Unknown'}")
    new_server = input("Enter new NTP server (hostname or IP): ").strip()
    if not new_server:
        return False
    if not re.fullmatch(r"[A-Za-z0-9._:-]+", new_server):
        logger.logger.error("Invalid NTP server value.")
        return False

    config_path = Path(TIMESYNCD_CONFIG)
    try:
        original_contents = config_path.read_text(encoding="utf-8")
        lines = original_contents.splitlines()
        backup_path = config_path.with_suffix(config_path.suffix + ".bak")
        if not backup_path.exists():
            shutil.copy2(config_path, backup_path)
    except OSError:
        logger.logger.exception("Could not read or back up %s.", config_path)
        return False

    section_start = None
    section_end = len(lines)
    for index, line in enumerate(lines):
        if line.strip().lower() == "[time]":
            section_start = index
            for end in range(index + 1, len(lines)):
                if lines[end].strip().startswith("["):
                    section_end = end
                    break
            break

    if section_start is None:
        lines.extend(["", "[Time]", f"NTP={new_server}"])
    else:
        setting_index = next(
            (
                index
                for index in range(section_start + 1, section_end)
                if re.match(r"\s*#?\s*NTP\s*=", lines[index], re.IGNORECASE)
            ),
            None,
        )
        if setting_index is None:
            lines.insert(section_end, f"NTP={new_server}")
        else:
            lines[setting_index] = f"NTP={new_server}"

    try:
        config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError:
        logger.logger.exception("Could not write %s.", config_path)
        try:
            config_path.write_text(original_contents, encoding="utf-8")
        except OSError:
            logger.logger.exception("Could not restore %s after a write failure.", config_path)
        return False

    if runner.run_command(["systemctl", "restart", "systemd-timesyncd"]) is None:
        try:
            config_path.write_text(original_contents, encoding="utf-8")
            runner.run_command(["systemctl", "restart", "systemd-timesyncd"])
        except OSError:
            logger.logger.exception("Could not roll back the NTP server configuration.")
        print("Failed to restart systemd-timesyncd.")
        return False
    logger.logger.info("NTP server changed to %s.", new_server)
    print("NTP server changed successfully.")
    return True


def _sync_ntp() -> bool:
    if _detect_ntp_service() != "systemd-timesyncd":
        print("NTP sync is supported only for systemd-timesyncd.")
        return False
    if runner.run_command(["systemctl", "restart", "systemd-timesyncd"]) is None:
        print("Failed to restart the time sync service.")
        return False

    for attempt in range(3):
        synchronized = _get_property("NTPSynchronized")
        if synchronized is None:
            return False
        if synchronized.lower() == "yes":
            print("NTP synchronized successfully.")
            logger.logger.info("NTP synchronized successfully.")
            return True
        if attempt < 2:
            time.sleep(5)

    print("NTP synchronization failed.")
    logger.logger.error("NTP synchronization failed.")
    return False
