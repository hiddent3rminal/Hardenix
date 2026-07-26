import os
from core import logger
from core import runner
import re
from pathlib import Path
import shutil
import ipaddress
import yaml

NAME = "network"

VERSION = "1.0.0"

DESCRIPTION = "network settings management Module"

SUPPORTED_DISTROS = [
    "ubuntu",
    "debian"
]

SERVICES = []

PACKAGES = []

# Network-related configuration files that should be considered for backup or hardening.
CONFIG_PATHS = [

    "/etc/netplan",

    "/etc/resolv.conf",

    "/etc/hosts",

    "/etc/hostname",

    "/etc/systemd/resolved.conf"
]

# Default sysctl values used by the hardening configuration.
# These settings disable common IPv4 attack vectors and improve host hardening.
SYSCTL_SETTINGS = {
    "net.ipv4.ip_forward": "0",
    "net.ipv4.conf.all.accept_redirects": "0",
    "net.ipv4.conf.default.accept_redirects": "0",
    "net.ipv4.conf.all.send_redirects": "0",
    "net.ipv4.conf.default.send_redirects": "0",
    "net.ipv4.conf.all.accept_source_route": "0",
    "net.ipv4.conf.default.accept_source_route": "0",
    "net.ipv4.conf.all.rp_filter": "1",
    "net.ipv4.conf.default.rp_filter": "1",
    "net.ipv4.tcp_syncookies": "1"
}


# Main and default functions
def check_existence():

    # Check whether network configuration files exist.
    # Return True if at least one configuration path exists.

    found = False

    # Scan every known network path and record whether it exists.
    for path in CONFIG_PATHS:

        if os.path.exists(path):

            logger.logger.debug(
                f"Network config found: {path}"
            )

            found = True

        else:

            logger.logger.debug(
                f"Network config missing: {path}"
            )


    # Report whether the host has any detectable network configuration files.
    if found:
        logger.logger.info(
            "Network configuration detected."
        )

    else:
        logger.logger.warning(
            "No network configuration files found."
        )


    return found




def install():

    # This module does not require a separate installation step.
    logger.logger.info(
        "Network module does not require installation."
    )

    return True



def configure():

    # Start the full network configuration workflow.
    logger.logger.info(
        "Network configuration started."
    )

    try:

        # Apply hostname, DNS, static IP, and kernel hardening in order.
        if not configure_hostname():
            logger.logger.error(
                "Hostname configuration failed."
            )
            return False


        if not configure_dns():
            logger.logger.error(
                "DNS configuration failed."
            )
            return False


        if not configure_ip_static():
            logger.logger.error(
                "Static IP configuration failed."
            )
            return False


        if not kernel_parameters():
            logger.logger.error(
                "Kernel network hardening failed."
            )
            return False


        # Collect a final status snapshot after all changes are applied.
        status()

        logger.logger.info(
            "Network configuration completed successfully."
        )

        return True


    except Exception as error:

        logger.logger.exception(
            f"Unexpected network configuration error: {error}"
        )

        return False

def backup():

    # Return the list of paths that should be copied into the backup archive.
    return CONFIG_PATHS



def restore():

    # Restore logic is not implemented yet.
    pass


def status():

    # Check the current network interface state.
    logger.logger.info(
        "Checking network connectivity."
    )

    # Run the system command to collect interface information.
    result = runner.run_command(
        ["ip", "addr"]
    )


    if result is None:

        logger.logger.error(
            "Failed to get network status."
        )

        return False


    logger.logger.info(
        "Network status collected."
    )

    return True


# Third-party style helper functions

def configure_hostname():

    # Start hostname configuration and read the current host name.
    logger.logger.info(
        "Hostname configuration started."
    )

    # Read the current hostname from the system.
    result = runner.run_command(
        ["hostname"]
    )

    if result is None or result.returncode != 0:
        logger.logger.error(
            "Failed to read current hostname."
        )
        return False


    current_hostname = result.stdout.strip()

    # Ask whether the user wants to change the hostname.
    choice = input(
        f"Current hostname: {current_hostname}\n"
        "Change hostname? (y/N): "
    ).strip().lower()


    if choice != "y":

        logger.logger.info(
            "Keeping current hostname."
        )

        return True



    # Read the new hostname from the user.
    new_hostname = input(
        "New hostname: "
    ).strip()



    if not new_hostname:

        logger.logger.error(
            "Hostname cannot be empty."
        )

        return False



    if new_hostname == current_hostname:

        logger.logger.info(
            "Hostname already configured."
        )

        return True



    hostname_pattern = (
        r"^[a-zA-Z0-9]"
        r"(?:[a-zA-Z0-9-]{0,61}"
        r"[a-zA-Z0-9])?$"
    )


    if not re.match(hostname_pattern, new_hostname):

        logger.logger.error(
            "Invalid hostname format."
        )

        return False



    # Apply the hostname change using systemd's hostnamectl command.
    result = runner.run_command(
        [
            "hostnamectl",
            "set-hostname",
            new_hostname
        ]
    )


    if result is None or result.returncode != 0:

        logger.logger.error(
            "Failed to change hostname."
        )

        return False



    try:

        # Update /etc/hosts so the new hostname resolves correctly locally.
        with open("/etc/hosts", "r") as file:

            lines = file.readlines()


        updated = False


        with open("/etc/hosts", "w") as file:

            for line in lines:

                parts = line.split()

                if parts and parts[0] == "127.0.1.1":

                    file.write(
                        f"127.0.1.1\t{new_hostname}\n"
                    )

                    updated = True

                else:

                    file.write(line)



            if not updated:

                file.write(
                    f"\n127.0.1.1\t{new_hostname}\n"
                )


    except Exception as error:

        logger.logger.exception(
            f"Failed to update /etc/hosts: {error}"
        )

        return False



    logger.logger.info(
        f"Hostname changed: {current_hostname} -> {new_hostname}"
    )


    return True



def configure_dns():

    # Start DNS configuration and prepare Netplan-related variables.
    logger.logger.info("DNS configuration started.")

    netplan_dir = Path("/etc/netplan")
    override_file = netplan_dir / "99-hardenix-dns.yaml"
    netplan_sections = ("ethernets", "wifis", "bonds", "bridges", "vlans", "tunnels")

    dns_presets = {
        "1": ("Cloudflare", ["1.1.1.1", "1.0.0.1"]),
        "2": ("Google", ["8.8.8.8", "8.8.4.4"]),
        "3": ("Quad9", ["9.9.9.9", "149.112.112.112"]),
        "4": ("Custom", []),
    }

    def parse_list(raw: str) -> list[str]:
        # Split a comma- or space-separated DNS input value into a clean list.
        return [item.strip() for item in raw.replace(",", " ").split() if item.strip()]

    def validate_dns_servers(servers: list[str]) -> list[str] | None:
        # Ensure each DNS server entry is a valid IP address before applying it.
        valid = []
        for server in servers:
            try:
                ipaddress.ip_address(server)
            except ValueError:
                logger.logger.error(f"Invalid DNS server IP: {server}")
                return None
            valid.append(server)
        return valid

    def detect_active_interface() -> str | None:
        # Detect the active network interface used for the default route.
        result = runner.run_command(["ip", "route", "show", "default"])
        if result and result.stdout:
            for line in result.stdout.splitlines():
                match = re.search(r"\bdev\s+(\S+)", line)
                if match:
                    iface = match.group(1)
                    if iface != "lo":
                        return iface

        result = runner.run_command(["ip", "-o", "link", "show", "up"])
        if result and result.stdout:
            for line in result.stdout.splitlines():
                match = re.match(r"\d+:\s+([^:@]+)", line)
                if match:
                    iface = match.group(1)
                    if iface != "lo":
                        return iface

        return None

    def guess_device_section(interface: str) -> str:
        # Determine whether the interface should be placed under ethernets, wifis, etc.
        result = runner.run_command(["networkctl", "status", interface])
        if result and result.stdout:
            text = result.stdout.lower()
            if "type: wifi" in text or "type: wireless" in text:
                return "wifis"
            if "type: ether" in text or "type: ethernet" in text:
                return "ethernets"
            if "type: bridge" in text:
                return "bridges"
            if "type: bond" in text:
                return "bonds"
            if "type: vlan" in text:
                return "vlans"
            if "type: tunnel" in text:
                return "tunnels"

        if interface.startswith(("wl", "wlan")):
            return "wifis"
        if interface.startswith("br"):
            return "bridges"
        if interface.startswith("bond"):
            return "bonds"
        if interface.startswith("vlan"):
            return "vlans"

        return "ethernets"

    def find_existing_netplan_target(interface: str) -> tuple[str | None, str | None]:
        # Find an existing Netplan file that already contains the selected interface.
        files = sorted(list(netplan_dir.glob("*.yaml")) + list(netplan_dir.glob("*.yml")))

        for path in files:
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
            except Exception as exc:
                logger.logger.warning(f"Could not read {path}: {exc}")
                continue

            network = data.get("network")
            if not isinstance(network, dict):
                continue

            for section in netplan_sections:
                section_map = network.get(section)
                if isinstance(section_map, dict) and interface in section_map:
                    return str(path), section

        return None, None

    def update_existing_yaml(path: str, section: str, interface: str,
                             dns_servers: list[str], search_domains: list[str]) -> bool:
        # Update an existing Netplan YAML file in place with the selected DNS values.
        try:
            p = Path(path)

            backup_path = p.with_suffix(p.suffix + ".bak")
            if not backup_path.exists():
                shutil.copy2(p, backup_path)

            with p.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            if not isinstance(data, dict):
                data = {}

            network = data.setdefault("network", {})
            if not isinstance(network, dict):
                data["network"] = network = {}

            section_map = network.setdefault(section, {})
            if not isinstance(section_map, dict):
                network[section] = section_map = {}

            device_cfg = section_map.setdefault(interface, {})

            if not isinstance(device_cfg, dict):
                section_map[interface] = device_cfg = {}

            device_cfg["dhcp4-overrides"] = {
                "use-dns": False
            }

            nameservers = device_cfg.setdefault("nameservers", {})
            if not isinstance(nameservers, dict):
                device_cfg["nameservers"] = nameservers = {}

            nameservers["addresses"] = dns_servers

            if search_domains:
                nameservers["search"] = search_domains
            else:
                nameservers.pop("search", None)

            with p.open("w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False)

            logger.logger.info(f"Updated DNS in existing Netplan file: {path}")
            return True

        except Exception as exc:
            logger.logger.exception(f"Failed to update existing Netplan file {path}: {exc}")
            return False

    def write_override_file(interface: str, section: str,
                            dns_servers: list[str], search_domains: list[str]) -> bool:
        # Create a dedicated Netplan override file when no existing target is found.
        try:
            lines = [
                "# Hardenix DNS override",
                "network:",
                "  version: 2",
                f"  {section}:",
                f"    {interface}:",
                "      dhcp4-overrides:",
                "        use-dns: false",
                "      nameservers:",
                "        addresses:",
            ]

            for server in dns_servers:
                lines.append(f"          - {server}")

            if search_domains:
                lines.append("        search:")
                for domain in search_domains:
                    lines.append(f"          - {domain}")

            content = "\n".join(lines) + "\n"

            if override_file.exists():
                backup_path = override_file.with_suffix(override_file.suffix + ".bak")
                if not backup_path.exists():
                    shutil.copy2(override_file, backup_path)

            override_file.write_text(content, encoding="utf-8")
            logger.logger.info(f"Wrote DNS override file: {override_file}")
            return True

        except Exception as exc:
            logger.logger.exception(f"Failed to write DNS override file: {exc}")
            return False

    # Prompt the user to choose a DNS preset or use a custom list.
    choice = input(
        "Choose DNS provider:\n"
        "  1) Cloudflare (1.1.1.1 / 1.0.0.1)\n"
        "  2) Google (8.8.8.8 / 8.8.4.4)\n"
        "  3) Quad9 (9.9.9.9 / 149.112.112.112)\n"
        "  4) Custom\n"
        "  Enter) Keep current\n"
        "Select: "
    ).strip()

    if choice == "":
        logger.logger.info("Keeping current DNS settings.")
        return True

    if choice not in dns_presets:
        logger.logger.error("Invalid DNS choice.")
        return False

    preset_name, preset_servers = dns_presets[choice]

    if choice == "4":
        raw_servers = input(
            "Enter DNS servers (space/comma separated, e.g. 1.1.1.1 8.8.8.8): "
        ).strip()
        dns_servers = parse_list(raw_servers)
    else:
        dns_servers = preset_servers
        logger.logger.info(f"Selected DNS preset: {preset_name}")

    dns_servers = validate_dns_servers(dns_servers)
    if not dns_servers:
        return False

    raw_search = input(
        "Search domains (optional, space/comma separated, Enter to skip): "
    ).strip()
    search_domains = parse_list(raw_search) if raw_search else []

    # Detect the active interface automatically; if that fails, ask the user.
    interface = detect_active_interface()
    if not interface:
        interface = input("Interface not detected automatically. Enter interface name: ").strip()

    if not interface:
        logger.logger.error("No interface selected.")
        return False

    section = guess_device_section(interface)
    logger.logger.info(f"Using interface '{interface}' in Netplan section '{section}'.")

    # Decide whether to update an existing Netplan entry or create a new override.
    target_path, target_section = find_existing_netplan_target(interface)

    if target_path:
        if not update_existing_yaml(target_path, target_section, interface, dns_servers, search_domains):
            return False
    else:
        if not write_override_file(interface, section, dns_servers, search_domains):
            return False

    # Regenerate and apply the Netplan configuration so the DNS values take effect.
    if runner.run_command(["netplan", "generate"]) is None:
        logger.logger.error("netplan generate failed.")
        return False

    if runner.run_command(["netplan", "apply"]) is None:
        logger.logger.error("netplan apply failed.")
        return False

    # Verify that the selected DNS servers are actually active.
    verify = runner.run_command(["resolvectl", "status"])

    if verify is None:
        logger.logger.error("failed to verify DNS status")
        return False

    for dns in dns_servers:
        if dns not in verify.stdout:
            logger.logger.error(f"DNS {dns} is not active")
            return False
    logger.logger.info("DNS verification successful")
    logger.logger.info(f"DNS configured successfully for {interface}.")
    return True




def configure_ip_static():

    # Static IP configuration is not implemented yet.
    pass

    

def kernel_parameters():

    # Build the configuration payload for sysctl hardening and hand it to the runner.
    config = {
        "file": "/etc/sysctl.d/99-hardenix.conf",
        "settings": SYSCTL_SETTINGS
    }
    return runner.apply_sysctl(config)




