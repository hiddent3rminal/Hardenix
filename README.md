# Hardenix
Interactive Linux server provisioning and hardening framework for Ubuntu and Debian.

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

The quick workflow currently backs up configuration, offers time settings,
and applies selected network settings. SSH hardening, Fail2Ban, firewall
configuration, static-IP configuration, and restore are not implemented and
are explicitly skipped or reported unavailable. Do not treat a completed run
as a full server-hardening audit.
