# Security policy

Hardenix is alpha software that runs with root privileges and can change
authentication, network, time, and package configuration. Do not deploy it on
production systems without independent review and testing on a disposable
Ubuntu/Debian host with console access.

## Reporting a vulnerability

Please do not report exploitable security issues in public GitHub issues.
Use GitHub's private vulnerability reporting for this repository. If private
reporting is unavailable, contact the repository maintainers privately through
GitHub before publishing details.

Include the affected commit/version, impact, prerequisites, and a minimal
reproduction that avoids real credentials or third-party systems. Do not
include secrets, private keys, or unredacted server configuration.

The maintainers will acknowledge a report as soon as reasonably possible,
assess severity and affected versions, and coordinate a fix and disclosure
timeline with the reporter. No response-time guarantee is made for this alpha
project.

## Security assumptions

- Run only a trusted checkout that untrusted users cannot modify.
- Registered modules are executable Python and inherit root privileges.
- Backups may contain sensitive system configuration; protect them accordingly.
- Automated tests mock system commands and are not proof of safe behavior on
  every distribution or server configuration.
