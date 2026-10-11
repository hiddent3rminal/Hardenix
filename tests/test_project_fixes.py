import importlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import call, patch

from core import backup, runner
from modules import network, system_update, timezone
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
        )

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
    @patch.object(
        network,
        "configure_ip_static",
        side_effect=AssertionError("must be skipped"),
    )
    def test_network_workflow_does_not_require_unimplemented_static_ip(
        self, static_ip, hostname, dns, kernel, status
    ):
        self.assertTrue(network.configure())
        static_ip.assert_not_called()
        hostname.assert_called_once()
        dns.assert_called_once()
        kernel.assert_called_once()

    def test_backup_module_list_has_no_missing_ufw_dependency(self):
        self.assertNotIn("modules.ufw", [service.__name__ for service in backup.SERVICES])

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


class SystemUpdateTests(unittest.TestCase):
    @patch.object(system_update.runner, "run_command")
    def test_updates_run_as_separate_argument_lists(self, run):
        run.side_effect = [
            subprocess.CompletedProcess([], 0, "", ""),
            subprocess.CompletedProcess([], 0, "", ""),
        ]

        self.assertTrue(system_update.update())
        self.assertEqual(
            run.call_args_list,
            [
                call(["apt-get", "update"]),
                call(["apt-get", "upgrade", "-y"]),
            ],
        )

    @patch.object(system_update.runner, "run_command", return_value=None)
    def test_update_stops_when_package_index_refresh_fails(self, run):
        self.assertFalse(system_update.update())
        run.assert_called_once_with(["apt-get", "update"])


if __name__ == "__main__":
    unittest.main()
