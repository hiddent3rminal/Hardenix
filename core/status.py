from core import logger, runner
from modules.registry import get_modules


def show_summary() -> bool:
    checks = (
        ("Hostname", ["hostname"]),
        ("Network interfaces", ["ip", "-brief", "address"]),
        ("Timezone", ["timedatectl", "show", "--property=Timezone"]),
        ("NTP enabled", ["timedatectl", "show", "--property=NTP"]),
        (
            "NTP synchronized",
            ["timedatectl", "show", "--property=NTPSynchronized"],
        ),
    )
    complete = True
    print("\nSystem status")
    for label, command in checks:
        result = runner.run_command(command)
        if result is None:
            print(f"{label}: unavailable")
            complete = False
            continue
        value = result.stdout.strip() or "unknown"
        print(f"{label}: {value}")

    print("\nService modules")
    for module in get_modules():
        try:
            if not module.status():
                complete = False
        except Exception:
            logger.logger.exception("Status check failed for module %s.", module.NAME)
            print(f"{module.NAME}: status check failed")
            complete = False
    return complete
