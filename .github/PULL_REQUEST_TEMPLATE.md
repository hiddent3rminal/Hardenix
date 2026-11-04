## Summary

<!-- Describe the change and its motivation. -->

## Validation

- [ ] `python -m unittest discover -v`
- [ ] `python -m compileall -q main.py core modules workflow templates tests`
- [ ] Added or updated tests for behavior changes
- [ ] Privileged or network-changing behavior is mocked in automated tests

## Safety and compatibility

- [ ] Configuration changes preserve unrelated settings
- [ ] Changes are validated before services are reloaded
- [ ] Failure paths restore prior state or report incomplete rollback
- [ ] README/module documentation reflects changed behavior
- [ ] No secrets, host-specific data, or generated artifacts are included
