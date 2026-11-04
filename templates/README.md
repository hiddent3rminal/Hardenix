# Creating a Hardenix module

1. Copy `module_template.py` to `modules/<service>.py`.
2. Set `NAME`, `VERSION`, `DESCRIPTION`, `SUPPORTED_DISTROS`, `PACKAGES`,
   `SERVICES`, and `CONFIG_PATHS`.
3. Implement `check_existence()`, `install()`, `configure()`, `backup()`, and
   `status()`; each returns a boolean except `backup()`, which returns paths.
4. Validate user input and supported distributions. Back up files before
   changing them, use atomic writes, verify service/configuration changes, and
   restore previous state when validation or application fails.
5. Add the imported module to `CUSTOM_MODULES` in `modules/registry.py`.
6. Add unit tests that mock commands and file paths; never test against the
   developer's live system.

Modules are imported from trusted source and run as root. Do not auto-discover
modules from writable directories or load code supplied by untrusted users.
The framework's generic backup and status actions use the registered module
contract; configuration-specific changes and recovery remain module-owned.