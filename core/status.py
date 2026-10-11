from core import runner


def show_summary() -> bool:
    # TODO: Include effective firewall, SSH, Fail2Ban, and kernel-hardening state.
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
    return complete
