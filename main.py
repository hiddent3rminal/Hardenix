import os
import shlex

from core import backup, banner, logger, status
from core.restore import restore_backup
from modules.registry import get_modules
from workflow import quick_setup


def clear_screen() -> None:
    print("\033[2J\033[H", end="")


def check_privilege() -> bool:
    if os.getuid() != 0:
        print("Hardenix must be run as root. Try: sudo python3 main.py")
        logger.logger.critical("Hardenix did not start with root privileges.")
        return False
    logger.logger.info("Hardenix started with root privileges.")
    return True


def detect_os() -> dict[str, str]:
    os_release = "/etc/os-release"
    info: dict[str, str] = {}
    try:
        with open(os_release, encoding="utf-8") as release_file:
            for line in release_file:
                key, separator, value = line.partition("=")
                if separator:
                    try:
                        parsed = shlex.split(value, comments=False, posix=True)
                    except ValueError:
                        logger.logger.warning("Could not parse %s value in %s.", key, os_release)
                        continue
                    info[key] = parsed[0] if parsed else ""
    except OSError:
        logger.logger.exception("Could not read operating-system information from %s.", os_release)
        return {"id": "unknown", "family": "unknown", "name": "Unknown OS"}

    os_id = info.get("ID", "unknown").lower()
    id_like = info.get("ID_LIKE", "").lower().split()
    name = info.get("PRETTY_NAME", "Unknown OS")
    family = "debian" if os_id in {"ubuntu", "debian"} or "debian" in id_like else "unknown"

    print(banner.ascii_art)
    print(f"Hardenix initialized on {name} ({family} family)")
    logger.logger.info("Detected operating system: %s (%s family).", name, family)
    return {"id": os_id, "family": family, "name": name}


def _choose_module(modules, action: str) -> None:
    if not modules:
        print("No modules provide this action.")
        return
    for index, module in enumerate(modules, start=1):
        print(f"{index}) {module.NAME} — {module.DESCRIPTION}")
    choice = input(f"Select a module to {action} (Enter to cancel): ").strip()
    if not choice:
        return
    if not choice.isdecimal() or not 1 <= int(choice) <= len(modules):
        print("Invalid module selection.")
        return

    module = modules[int(choice) - 1]
    try:
        succeeded = getattr(module, action)()
    except Exception:
        logger.logger.exception("%s failed for module %s.", action, module.NAME)
        print(f"{action.capitalize()} failed for {module.NAME}; check the log.")
        return
    if succeeded:
        print(f"{module.NAME}: {action} completed.")
    else:
        print(f"{module.NAME}: {action} failed; check the log.")


def _create_backup() -> None:
    backup_path = backup.create_backup()
    if backup_path is False:
        print("Backup failed or was incomplete.")
        return
    try:
        archive = backup.compress_folder(backup_path)
    except OSError:
        logger.logger.exception("Could not compress the backup.")
        print("Backup was created, but compression failed.")
        return
    print(f"Backup created: {archive}")


def main_menu(system: dict[str, str]) -> None:
    modules = get_modules()
    installable_modules = [module for module in modules if module.PACKAGES]
    while True:
        print(f"\nDetected system: {system['name']} ({system['family']} family)\n")
        print("1) Quick setup (backup, timezone, SSH, Fail2Ban, network)")
        print("2) Configure a module")
        print("3) Install a service")
        print("4) Check and apply system updates")
        print("5) Create a configuration backup")
        print("6) System status summary")
        print("7) Module development guide")
        print("8) Exit")
        choice = input("Select an option (1-8): ").strip()

        if choice == "1":
            if not quick_setup.quick_basic_hardening():
                print("Quick setup did not complete. Check the log for details.")
        elif choice == "2":
            _choose_module(
                [module for module in modules if module.NAME != "system packages"],
                "configure",
            )
        elif choice == "3":
            _choose_module(installable_modules, "install")
        elif choice == "4":
            package_module = next(
                module for module in modules if module.NAME == "system packages"
            )
            _choose_module([package_module], "configure")
        elif choice == "5":
            _create_backup()
        elif choice == "6":
            if not status.show_summary():
                print("Some status checks were unavailable.")
        elif choice == "7":
            action = input(
                "1) Restore a validated Hardenix backup\n"
                "2) Read the module development guide\n"
                "Select: "
            ).strip()
            if action == "1":
                path = input("Backup directory under /var/backups/hardenix: ").strip()
                if not restore_backup(path):
                    print("Restore failed. Check the log for details.")
            elif action == "2":
                print("Create a trusted Python module from templates/module_template.py.")
                print("Register it in modules/registry.py; registered modules run as root.")
            else:
                print("Invalid option.")
        elif choice == "8":
            logger.logger.info("Hardenix stopped.")
            clear_screen()
            return
        else:
            print("Please choose a valid option from 1 to 8.")


def main() -> int:
    logger.logger.info("Hardenix started.")
    if not check_privilege():
        return 1
    system = detect_os()
    if system["family"] != "debian":
        print("Unsupported operating system. Hardenix currently supports Ubuntu and Debian.")
        logger.logger.error("Unsupported operating system: %s.", system["id"])
        return 1
    main_menu(system)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
