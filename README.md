# Hardenix

Hardenix is a modular, interactive configuration and hardening tool for
Ubuntu/Debian servers. Its built-in modules cover time and NTP, OpenSSH,
Fail2Ban, network settings, and APT updates. You can add trusted service
modules, such as Apache or Samba, using the template and registry.

> Hardenix changes system-wide settings and must be run as root. Test in a
> disposable VM with console access first. Network, SSH, time, firewall, and
> package changes can interrupt service or lock out remote administrators.

## Requirements

- Ubuntu or Debian with systemd
- Python 3.10+
- Root/sudo privileges for system changes
- `python3-prompt-toolkit` and `python3-yaml`
- Standard system tools used by the selected module (for example `ip`,
  `netplan`, `resolvectl`, `timedatectl`, `sshd`, `fail2ban-client`, and APT)

Install and launch from a trusted checkout:

```sh
sudo apt update
sudo apt install python3-prompt-toolkit python3-yaml
git clone https://github.com/hiddent3rminal/Hardenix.git
cd Hardenix
sudo python3 main.py
```

Only run a trusted checkout that untrusted users cannot modify. The selected
Python interpreter must be able to import the OS-provided dependencies.

To run the test suite or build a local wheel for review, use an unprivileged
development environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m unittest discover -v
python -m pip wheel --no-deps --wheel-dir dist .
```

Do not install the application into the system Python with `sudo pip`; use the
distribution packages for runtime dependencies and launch the trusted checkout
with sudo as shown above.

## Features

- **Timezone:** select a system timezone, set time, manage NTP, and request a
  sync using systemd time utilities.
- **SSH:** inspect effective daemon settings, optionally change root login,
  password authentication, and maximum authentication attempts; validate with
  `sshd -t`, verify effective values, and reload an active daemon. Disabling
  password authentication requires a separate explicit confirmation.
- **Fail2Ban:** install on request and configure/validate an SSH jail.
- **Network:** optionally change hostname, configure DNS using Netplan, and
  apply selected sysctl network hardening settings. An opt-in static IPv4 flow
  updates an existing Netplan interface, preserves IPv6 addresses/routes,
  validates the generated configuration, applies it, and checks active state.
- **System updates:** refresh APT indexes, show simulated available upgrades,
  and ask before upgrading packages.
- **Backups and status:** create a root-private configuration backup with a
  manifest and archive; inspect built-in modules and selected system state.

The quick setup backs up configuration first, then offers the timezone, SSH,
Fail2Ban, and network module workflows. It stops on failures and reports a
limited status summary. It is not a full security audit or compliance scanner.
Uninstalled SSH and Fail2Ban are offered for installation and can be skipped.

Backups are stored under `/var/backups/hardenix`. Restore validates the
manifest and restricts destinations to paths declared by registered modules.
It requires typing `RESTORE` because current configuration will be overwritten.
Keep independent backups and verify recovery on a test system; this tool does
not promise a machine-wide transactional rollback.

## Add a service module

1. Copy `templates/module_template.py` to `modules/<service>.py`.
2. Implement the module contract: `NAME`, `VERSION`, `DESCRIPTION`,
   `SUPPORTED_DISTROS`, `PACKAGES`, `SERVICES`, `check_existence()`, `install()`,
   `configure()`, `backup()`, and `status()`.
3. Validate inputs and platform assumptions. Back up before changing state,
   write configuration atomically, validate it with the service's native
   checker, and restore the old state if applying the change fails.
4. Add the imported module to `CUSTOM_MODULES` in `modules/registry.py`.
5. Add tests that mock commands and temporary paths. Do not test by changing a
   developer's or production host.

Modules are executable Python code and run with Hardenix's root privileges.
For that reason, modules are explicitly registered rather than auto-discovered
from directories that may be writable by untrusted users. See
[`templates/README.md`](templates/README.md) for the module guide.

## Development and tests

Run the test suite without changing the host:

```sh
python3 -m unittest discover -v
python3 -m compileall -q main.py core modules workflow templates
```

Tests mock system commands and use temporary files where practical. Exercise
privileged operations separately in disposable Ubuntu/Debian VMs before
releasing changes.

## Current boundaries

- No UFW/firewall module, arbitrary service autodiscovery, or compliance
  certification.
- Static addressing is limited to IPv4 and an existing interface-name Netplan
  entry; it does not create network definitions or support NetworkManager-only
  hosts.
- Custom modules must be trusted, registered, and tested by their author.
- Restore covers only manifest-listed paths declared by registered modules;
  it does not restore runtime state or undo every side effect.
- The project is not a substitute for console access, backups, change review,
  or a tested incident-recovery plan.

See [LICENSE](LICENSE) for license terms.

Hardenix is currently an **alpha** release. See [SECURITY.md](SECURITY.md) for
responsible vulnerability reporting, [CONTRIBUTING.md](CONTRIBUTING.md) for
development and pull-request guidance, and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
for participation expectations.
