# Contributing

Thanks for helping improve Hardenix. Changes to this project may affect
root-owned configuration and remote server access; correctness and safe
failure behavior are more important than minimizing a diff.

## Before opening an issue or pull request

- Search existing issues and pull requests.
- Use sanitized examples; do not attach private hostnames, IP addresses,
  credentials, SSH keys, or unsanitized configuration/log files.
- For a new module, describe supported distributions, package/service
  dependencies, configuration paths, validation, and recovery behavior.

## Development setup

Use an unprivileged virtual environment. Never run unit tests with sudo.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m unittest discover -v
python -m compileall -q main.py core modules workflow templates tests
python -m pip wheel --no-deps --wheel-dir dist .
```

Tests must mock external commands and use temporary directories. Do not apply
configuration changes to a developer workstation or production server during
automated tests.

## Module requirements

- Add modules by explicit import and registration in `modules/registry.py`.
- Implement the documented module contract and declare supported distributions.
- Validate user-provided values and avoid shell command strings.
- Take a backup before writing; write atomically where possible.
- Use a service-native syntax check before reload/apply, then verify effective
  state.
- Preserve unrelated settings; roll back on failure and log any failed rollback.
- Require clear confirmation for disruptive actions, especially network and
  authentication changes.
- Add unit tests for success, validation failure, cancellation, and rollback.

## Pull requests

Keep changes focused, update user-facing documentation, and complete the pull
request checklist. CI must pass. Real privileged integration checks belong in
disposable Ubuntu/Debian VMs with console access and must not be represented as
covered by mocked unit tests.
