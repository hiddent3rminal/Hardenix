# Hardenix
Interactive Linux server provisioning and hardening framework for Ubuntu and Debian.

## Status 

Now It's Stopped Because Of Some Reasons, But PR Is Accpeted

## Requirements

- Ubuntu or Debian
- Python 3.10 or newer
- Root privileges for system changes

Install the Python dependencies from Ubuntu/Debian packages:

```sh
sudo apt update
sudo apt install python3-prompt-toolkit python3-yaml
sudo python3 main.py
```

The Python interpreter used for the system packages must be Python 3.10 or newer.
Run Hardenix only from a trusted checkout that untrusted users cannot modify;
the application needs root privileges to change system configuration.

## Current limitations

The quick workflow currently backs up configuration, offers time settings,
and applies selected network settings. It is not a complete hardening audit.

- SSH hardening, Fail2Ban configuration, and firewall/UFW support are not
  implemented; the quick workflow explicitly skips them.
- Static-IP configuration is not implemented.
- Backup restore is not implemented; restore options make no changes.
- Installed-service hardening and service installation menu actions are
  informational placeholders.
- The package updater exists but is not exposed in the menu and still needs
  explicit operator confirmation before upgrades.
- The status summary does not yet verify SSH, Fail2Ban, firewall, or all
  effective kernel-hardening settings.

Network and time changes require root and can affect remote access. Test them
on a disposable machine with console access before using them on a production
host.
