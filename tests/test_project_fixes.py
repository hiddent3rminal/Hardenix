import importlib
import ipaddress
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import call, patch

import yaml

from core import backup, runner
from modules import fail2ban, network, ssh, system_update, timezone
from modules.registry import get_modules
from workflow import quick_setup


class CommandRunnerTests(unittest.TestCase):
    @patch("core.runner.subprocess.run")
    def test_run_command_uses_argument_list(self, run):
        expected = subprocess.CompletedProcess(["echo", "ok"], 0, "ok\n", "")
        run.return_value = expected

        self.assertIs(runner.run_command(["echo", "ok"]), expected)
        run.assert_called_once_with(
            ["echo", "ok"],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )

    @patch("core.runner.subprocess.run")
    def test_run_command_applies_custom_timeout(self, run):
        run.return_value = subprocess.CompletedProcess(["apt-get"], 0, "", "")

        runner.run_command(["apt-get", "upgrade"], timeout=1800)

        self.assertEqual(run.call_args.kwargs["timeout"], 1800)

    @patch("core.runner.subprocess.run")
    def test_run_command_merges_environment_overrides(self, run):
        run.return_value = subprocess.CompletedProcess(["locale"], 0, "", "")

        runner.run_command(["locale"], env={"LC_ALL": "C"})

        environment = run.call_args.kwargs["env"]
        self.assertEqual(environment["LC_ALL"], "C")
        self.assertIn("PATH", environment)

    @patch(
        "core.runner.subprocess.run",
        side_effect=subprocess.TimeoutExpired(["sleep", "2"], 1),
    )
    def test_run_command_reports_timeout_as_failure(self, run):
        self.assertIsNone(runner.run_command(["sleep", "2"], timeout=1))
        run.assert_called_once()

    def test_run_command_rejects_shell_string(self):
        with self.assertRaises(ValueError):
            runner.run_command("echo unsafe")

    @patch(
        "core.runner.run_command",
        side_effect=[None, subprocess.CompletedProcess([], 0, "", "")],
    )
    def test_sysctl_failure_restores_previous_config(self, run):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "99-hardenix.conf"
            original = b"# previous values\nnet.ipv4.ip_forward = 1\n"
            config_path.write_bytes(original)

            result = runner.apply_sysctl(
                {
                    "file": str(config_path),
                    "settings": {"net.ipv4.ip_forward": "0"},
                }
            )

            self.assertFalse(result)
            self.assertEqual(config_path.read_bytes(), original)
            self.assertEqual(run.call_count, 2)


class WorkflowTests(unittest.TestCase):
    def test_main_imports_without_timezone_circular_import(self):
        main = importlib.import_module("main")
        self.assertTrue(callable(main.detect_os))

    def test_step_does_not_treat_none_as_success(self):
        self.assertFalse(quick_setup.run_step("empty", lambda: None))
        self.assertTrue(quick_setup.run_step("complete", lambda: True))

    @patch.object(network, "status", return_value=True)
    @patch.object(network, "kernel_parameters", return_value=True)
    @patch.object(network, "configure_dns", return_value=True)
    @patch.object(network, "configure_hostname", return_value=True)
    @patch.object(network, "configure_ip_static", return_value=True)
    def test_network_workflow_offers_static_ip_setup(
        self, static_ip, hostname, dns, kernel, _status
    ):
        self.assertTrue(network.configure())
        static_ip.assert_called_once()
        hostname.assert_called_once()
        dns.assert_called_once()
        kernel.assert_called_once()
        _status.assert_called_once()

    def test_backup_module_list_has_no_missing_ufw_dependency(self):
        self.assertNotIn("modules.ufw", [service.__name__ for service in backup.SERVICES])

    def test_registry_contains_expected_builtin_services(self):
        self.assertEqual(
            {module.NAME for module in get_modules()},
            {"timezone", "SSH", "Fail2Ban", "network", "system packages"},
        )

    def test_registry_rejects_malformed_custom_module(self):
        from modules import registry

        malformed = SimpleNamespace(
            __name__="modules.bad",
            NAME="Bad module",
            VERSION="1.0",
            DESCRIPTION="Invalid custom module",
            SUPPORTED_DISTROS="ubuntu",
            PACKAGES=[],
            SERVICES=[],
            check_existence=lambda: True,
            install=lambda: True,
            configure=lambda: True,
            backup=lambda: [],
            status=lambda: True,
        )
        with patch.object(registry, "CUSTOM_MODULES", (malformed,)):
            with self.assertRaisesRegex(ValueError, "SUPPORTED_DISTROS"):
                registry.get_modules()

    @patch.object(backup, "copy_config", return_value=False)
    @patch.object(backup, "create_backup_folder")
    @patch.object(backup, "SERVICES")
    def test_backup_fails_when_a_copy_fails(self, services, create_folder, copy_config):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "config"
            source.write_text("data", encoding="utf-8")
            services.__iter__.return_value = iter(
                [
                    SimpleNamespace(
                        __name__="modules.fake",
                        check_existence=lambda: True,
                        backup=lambda: [str(source)],
                    )
                ]
            )
            create_folder.return_value = directory

            self.assertIs(backup.create_backup(), False)
            copy_config.assert_called_once()


class TimezoneTests(unittest.TestCase):
    @patch.object(timezone.runner, "run_command", return_value=None)
    def test_timedatectl_failure_is_returned_as_missing_property(self, run):
        self.assertIsNone(timezone._get_property("NTP"))
        run.assert_called_once()

    @patch.object(timezone, "_detect_ntp_service", return_value="chrony")
    def test_unsupported_ntp_sync_fails_cleanly(self, detect_service):
        self.assertFalse(timezone._sync_ntp())
        detect_service.assert_called_once()

    @patch("builtins.input", side_effect=["2026-11-04", "10:00:00"])
    @patch.object(timezone, "_get_property", return_value="yes")
    @patch.object(
        timezone.runner,
        "run_command",
        side_effect=[
            subprocess.CompletedProcess([], 0, "", ""),
            subprocess.CompletedProcess([], 0, "", ""),
            subprocess.CompletedProcess([], 0, "", ""),
        ],
    )
    def test_manual_time_change_restores_enabled_ntp(
        self, run, _get_property_mock, _input_mock
    ):
        self.assertTrue(timezone._change_time_manually())
        _get_property_mock.assert_called_once_with("NTP")
        self.assertEqual(_input_mock.call_count, 2)
        self.assertEqual(
            run.call_args_list,
            [
                call(["timedatectl", "set-ntp", "false"]),
                call(["timedatectl", "set-time", "2026-11-04 10:00:00"]),
                call(["timedatectl", "set-ntp", "true"]),
            ],
        )


class NetworkTests(unittest.TestCase):
    def test_hosts_update_preserves_aliases_and_comments(self):
        with tempfile.TemporaryDirectory() as directory:
            hosts = Path(directory) / "hosts"
            hosts.write_text(
                "127.0.1.1 old-host alias # local host\n"
                "127.0.0.1 localhost\n",
                encoding="utf-8",
            )

            network._update_hosts_hostname(hosts, "old-host", "new-host")

            self.assertEqual(
                hosts.read_text(encoding="utf-8"),
                "127.0.1.1\tnew-host alias # local host\n"
                "127.0.0.1 localhost\n",
            )

    def test_hosts_update_adds_entry_when_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            hosts = Path(directory) / "hosts"
            hosts.write_text("127.0.0.1 localhost", encoding="utf-8")

            network._update_hosts_hostname(hosts, "old-host", "new-host")

            self.assertEqual(
                hosts.read_text(encoding="utf-8"),
                "127.0.0.1 localhost\n127.0.1.1\tnew-host\n",
            )

    def test_static_ipv4_updates_netplan_without_dropping_ipv6(self):
        with tempfile.TemporaryDirectory() as directory:
            netplan_dir = Path(directory)
            config_file = netplan_dir / "01-netcfg.yaml"
            config_file.write_text(
                "network:\n"
                "  version: 2\n"
                "  ethernets:\n"
                "    eth0:\n"
                "      dhcp4: true\n"
                "      addresses:\n"
                "        - 2001:db8::10/64\n"
                "        - 192.0.2.10/24\n"
                "      routes:\n"
                "        - to: default\n"
                "          via: 192.0.2.1\n"
                "        - to: default\n"
                "          via: 2001:db8::1\n",
                encoding="utf-8",
            )
            command_results = [
                subprocess.CompletedProcess([], 0, "", ""),
                subprocess.CompletedProcess([], 0, "", ""),
                subprocess.CompletedProcess(
                    [], 0, "2: eth0 inet 192.0.2.20/24 scope global eth0", ""
                ),
                subprocess.CompletedProcess(
                    [], 0, "default via 192.0.2.254 dev eth0", ""
                ),
            ]
            with (
                patch.object(network, "NETPLAN_DIR", netplan_dir),
                patch.object(network.runner, "run_command", side_effect=command_results),
                patch(
                    "builtins.input",
                    side_effect=[
                        "y",
                        "eth0",
                        "192.0.2.20/24",
                        "192.0.2.254",
                        "1.1.1.1",
                        "APPLY STATIC IP",
                    ],
                ),
            ):
                self.assertTrue(network.configure_ip_static())

            updated = yaml.safe_load(config_file.read_text(encoding="utf-8"))
            device = updated["network"]["ethernets"]["eth0"]
            self.assertFalse(device["dhcp4"])
            self.assertIn("2001:db8::10/64", device["addresses"])
            self.assertIn("192.0.2.20/24", device["addresses"])
            self.assertIn(
                {"to": "default", "via": "2001:db8::1"},
                device["routes"],
            )
            self.assertIn(
                {"to": "default", "via": "192.0.2.254"},
                device["routes"],
            )
            self.assertTrue(config_file.with_suffix(".yaml.hardenix.bak").is_file())

    def test_static_ipv4_restores_original_netplan_when_generation_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            netplan_dir = Path(directory)
            config_file = netplan_dir / "01-netcfg.yaml"
            original = (
                "network:\n"
                "  version: 2\n"
                "  ethernets:\n"
                "    eth0:\n"
                "      dhcp4: true\n"
            )
            config_file.write_text(original, encoding="utf-8")
            with (
                patch.object(network, "NETPLAN_DIR", netplan_dir),
                patch.object(
                    network.runner,
                    "run_command",
                    side_effect=[
                        None,
                        subprocess.CompletedProcess([], 0, "", ""),
                    ],
                ) as run,
                patch(
                    "builtins.input",
                    side_effect=[
                        "y",
                        "eth0",
                        "192.0.2.20/24",
                        "192.0.2.1",
                        "",
                        "APPLY STATIC IP",
                    ],
                ),
            ):
                self.assertFalse(network.configure_ip_static())

            self.assertEqual(config_file.read_text(encoding="utf-8"), original)
            self.assertEqual(
                run.call_args_list,
                [
                    call(["netplan", "generate"]),
                ],
            )

    def test_static_ipv4_verification_requires_exact_address_and_prefix(self):
        configured = ipaddress.IPv4Interface("192.0.2.2/24")
        self.assertFalse(
            network._is_static_ipv4_active(
                "2: eth0 inet 192.0.2.20/24 scope global eth0",
                configured,
            )
        )


class SSHTests(unittest.TestCase):
    def test_ssh_configuration_writes_only_requested_settings(self):
        effective = [
            {
                "permitrootlogin": "prohibit-password",
                "passwordauthentication": "yes",
                "maxauthtries": "6",
            },
            {
                "permitrootlogin": "no",
                "passwordauthentication": "yes",
                "maxauthtries": "6",
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "sshd_config"
            drop_in = Path(directory) / "sshd_config.d" / "99-hardenix.conf"
            config_file.write_text(
                "Include /etc/ssh/sshd_config.d/*.conf\n",
                encoding="utf-8",
            )
            with (
                patch.object(ssh, "CONFIG_FILE", config_file),
                patch.object(ssh, "DROP_IN", drop_in),
                patch.object(ssh, "check_existence", return_value=True),
                patch.object(ssh, "_effective_settings", side_effect=effective),
                patch.object(ssh, "_reload_service", return_value=True),
                patch.object(ssh.runner, "run_command", return_value=subprocess.CompletedProcess([], 0, "", "")),
                patch("builtins.input", side_effect=["no", "", "", "y"]),
            ):
                self.assertTrue(ssh.configure())

            self.assertEqual(
                drop_in.read_text(encoding="utf-8"),
                "# Managed by Hardenix; local changes will be replaced.\n"
                "PermitRootLogin no\n",
            )

    def test_ssh_settings_roll_back_when_validation_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "sshd_config"
            drop_in = Path(directory) / "sshd_config.d" / "99-hardenix.conf"
            config_file.write_text(
                "Include /etc/ssh/sshd_config.d/*.conf\n",
                encoding="utf-8",
            )
            drop_in.parent.mkdir()
            drop_in.write_text("PermitRootLogin prohibit-password\n", encoding="utf-8")
            effective = {
                "permitrootlogin": "prohibit-password",
                "passwordauthentication": "yes",
                "maxauthtries": "6",
            }
            with (
                patch.object(ssh, "CONFIG_FILE", config_file),
                patch.object(ssh, "DROP_IN", drop_in),
                patch.object(ssh, "check_existence", return_value=True),
                patch.object(ssh, "_effective_settings", return_value=effective),
                patch.object(ssh, "_reload_service", return_value=True),
                patch.object(
                    ssh.runner,
                    "run_command",
                    side_effect=[
                        None,
                        subprocess.CompletedProcess([], 0, "", ""),
                    ],
                ),
                patch("builtins.input", side_effect=["no", "", "", "y"]),
            ):
                self.assertFalse(ssh.configure())

            self.assertEqual(
                drop_in.read_text(encoding="utf-8"),
                "PermitRootLogin prohibit-password\n",
            )


class SystemUpdateTests(unittest.TestCase):
    @patch.object(system_update.runner, "run_command")
    def test_updates_run_as_separate_argument_lists(self, run):
        run.side_effect = [
            subprocess.CompletedProcess([], 0, "", ""),
            subprocess.CompletedProcess([], 0, "2 upgraded, 0 newly installed\n", ""),
            subprocess.CompletedProcess([], 0, "", ""),
        ]

        with patch("builtins.input", return_value="y"):
            self.assertTrue(system_update.update())
        self.assertEqual(
            run.call_args_list,
            [
                call(["apt-get", "update"], timeout=1800),
                call(["apt-get", "-s", "upgrade"], env={"LC_ALL": "C"}),
                call(["apt-get", "upgrade", "-y"], timeout=1800),
            ],
        )

    @patch.object(system_update.runner, "run_command", return_value=None)
    def test_update_stops_when_package_index_refresh_fails(self, run):
        self.assertFalse(system_update.update())
        run.assert_called_once_with(["apt-get", "update"], timeout=1800)

    @patch.object(
        system_update.runner,
        "run_command",
        side_effect=[
            subprocess.CompletedProcess([], 0, "", ""),
            subprocess.CompletedProcess([], 0, "3 upgraded, 0 newly installed\n", ""),
        ],
    )
    @patch("builtins.input", return_value="n")
    def test_update_does_not_upgrade_without_confirmation(self, _prompt, run):
        self.assertTrue(system_update.update())
        self.assertEqual(run.call_count, 2)
        _prompt.assert_called_once()


class RestoreTests(unittest.TestCase):
    def test_restore_rejects_unregistered_destination(self):
        from core import restore

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "backups"
            backup_path = root / "test"
            backup_path.mkdir(parents=True)
            (backup_path / "payload").write_text("data", encoding="utf-8")
            (backup_path / "manifest.json").write_text(
                '{"version": 1, "entries": [{"backup": "payload", '
                '"source": "/tmp/not-registered"}]}',
                encoding="utf-8",
            )
            with patch.object(restore, "BACKUP_ROOT", root):
                self.assertFalse(restore.restore_backup(str(backup_path)))

    def test_restore_applies_registered_file_from_manifest(self):
        from core import restore

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "backups"
            backup_path = root / "test"
            backup_path.mkdir(parents=True)
            payload = backup_path / "payload"
            payload.write_text("restored", encoding="utf-8")
            destination = Path(directory) / "managed.conf"
            destination.write_text("old", encoding="utf-8")
            (backup_path / "manifest.json").write_text(
                json_manifest(payload.name, destination),
                encoding="utf-8",
            )
            module = SimpleNamespace(backup=lambda: [str(destination)])
            with (
                patch.object(restore, "BACKUP_ROOT", root),
                patch.object(restore, "get_modules", return_value=[module]),
                patch("builtins.input", return_value="RESTORE"),
            ):
                self.assertTrue(restore.restore_backup(str(backup_path)))
            self.assertEqual(destination.read_text(encoding="utf-8"), "restored")

    def test_restore_rejects_non_string_destination(self):
        from core import restore

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "backups"
            backup_path = root / "test"
            backup_path.mkdir(parents=True)
            (backup_path / "payload").write_text("data", encoding="utf-8")
            (backup_path / "manifest.json").write_text(
                '{"version": 1, "entries": [{"backup": "payload", "source": 123}]}',
                encoding="utf-8",
            )
            with patch.object(restore, "BACKUP_ROOT", root):
                self.assertFalse(restore.restore_backup(str(backup_path)))

    def test_restore_preserves_registered_destination_symlink(self):
        from core import restore

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "backups"
            backup_path = root / "test"
            backup_path.mkdir(parents=True)
            (backup_path / "payload").write_text("restored", encoding="utf-8")
            target = Path(directory) / "actual.conf"
            target.write_text("old", encoding="utf-8")
            link = Path(directory) / "managed.conf"
            link.symlink_to(target)
            (backup_path / "manifest.json").write_text(
                json_manifest("payload", link),
                encoding="utf-8",
            )
            module = SimpleNamespace(backup=lambda: [str(link)])
            with (
                patch.object(restore, "BACKUP_ROOT", root),
                patch.object(restore, "get_modules", return_value=[module]),
                patch("builtins.input", return_value="RESTORE"),
            ):
                self.assertTrue(restore.restore_backup(str(backup_path)))
            self.assertTrue(link.is_symlink())
            self.assertEqual(target.read_text(encoding="utf-8"), "restored")

    def test_restore_rejects_config_symlink_changed_since_backup(self):
        from core import restore

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "backups"
            backup_path = root / "test"
            backup_path.mkdir(parents=True)
            (backup_path / "payload").write_text("restored", encoding="utf-8")
            original_target = Path(directory) / "original.conf"
            changed_target = Path(directory) / "changed.conf"
            original_target.write_text("original", encoding="utf-8")
            changed_target.write_text("must remain", encoding="utf-8")
            link = Path(directory) / "managed.conf"
            link.symlink_to(original_target)
            (backup_path / "manifest.json").write_text(
                json_manifest("payload", original_target),
                encoding="utf-8",
            )
            link.unlink()
            link.symlink_to(changed_target)
            module = SimpleNamespace(backup=lambda: [str(link)])
            with (
                patch.object(restore, "BACKUP_ROOT", root),
                patch.object(restore, "get_modules", return_value=[module]),
            ):
                self.assertFalse(restore.restore_backup(str(backup_path)))
            self.assertEqual(changed_target.read_text(encoding="utf-8"), "must remain")


def json_manifest(backup_name: str, destination: Path) -> str:
    return json.dumps(
        {
            "version": 1,
            "entries": [{"backup": backup_name, "source": str(destination)}],
        }
    )


class Fail2BanTests(unittest.TestCase):
    def test_configuration_writes_validated_managed_jail(self):
        with tempfile.TemporaryDirectory() as directory:
            jail_file = Path(directory) / "jail.d" / "99-hardenix.local"
            with (
                patch.object(fail2ban, "JAIL_FILE", jail_file),
                patch.object(fail2ban, "check_existence", return_value=True),
                patch.object(
                    fail2ban.runner,
                    "run_command",
                    side_effect=[
                        subprocess.CompletedProcess([], 0, "", ""),
                        subprocess.CompletedProcess([], 0, "", ""),
                        subprocess.CompletedProcess([], 0, "Jail list: sshd\n", ""),
                    ],
                ) as run,
                patch("builtins.input", return_value="y"),
            ):
                self.assertTrue(fail2ban.configure())
            self.assertIn("[sshd]", jail_file.read_text(encoding="utf-8"))
            self.assertEqual(
                run.call_args_list,
                [
                    call(["fail2ban-client", "-t"]),
                    call(["systemctl", "enable", "--now", "fail2ban"]),
                    call(["fail2ban-client", "status", "sshd"]),
                ],
            )


if __name__ == "__main__":
    unittest.main()
