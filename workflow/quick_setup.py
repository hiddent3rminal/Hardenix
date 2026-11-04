# workflow/quick_setup.py


from collections.abc import Callable
from types import ModuleType

from modules.registry import get_module

from core import logger
from core import backup
from core import status



def run_step(name: str, function: Callable[[], bool | str | None]) -> bool:
    """
    Execute a hardening step safely.

    Args:
        name (str): Step name for logging
        function (callable): Function to execute

    Returns:
        bool: True if successful, False otherwise
    """

    logger.logger.info(
        f"Starting {name} configuration..."
    )

    try:

        result = function()


        if result is False or result is None:

            logger.logger.error(
                f"{name} configuration failed."
            )

            return False


        logger.logger.info(
            f"{name} configuration completed successfully."
        )

        return True


    except Exception as error:

        logger.logger.exception(
            f"{name} crashed with exception: {error}"
        )

        return False





def quick_basic_hardening():
    """
    Execute Hardenix basic hardening workflow.

    Order:
        1. Create backup
        2. Configure timezone
        3. Configure network
        4. Show final status

    Returns:
        bool:
            True  -> completed successfully
            False -> failed
    """


    logger.logger.info(
        "========== Quick Basic Hardening Started =========="
    )


    module_names = ("timezone", "ssh", "fail2ban", "network")
    steps: list[tuple[str, Callable[[], bool | str | None]]] = [
        ("Backup", backup.create_backup)
    ]
    for module_name in module_names:
        module = get_module(module_name)
        if module is None:
            logger.logger.error("Required built-in module is missing: %s", module_name)
            return False
        steps.append((module.NAME, lambda module=module: _configure_module(module)))

    for name, function in steps:
        if not run_step(name, function):
            logger.logger.critical(
                f"Quick hardening stopped during: {name}"
            )
            logger.logger.info(
                "System was not fully hardened."
            )
            return False
    logger.logger.info(
        "Running final system status check..."
    )
    try:
        if not status.show_summary():
            logger.logger.error("Final system status check was incomplete.")
            return False
    except Exception:
        logger.logger.exception(
            "Status check failed."
        )
        return False
    logger.logger.info(
        "========== Quick Basic Hardening Completed Successfully =========="
    )


    return True


def _configure_module(module: ModuleType) -> bool:
    if module.NAME.casefold() in {"ssh", "fail2ban"} and not module.check_existence():
        answer = input(
            f"{module.NAME} is not installed. Install it now? (y/N): "
        ).strip().lower()
        if answer != "y":
            logger.logger.info("%s setup skipped by user.", module.NAME)
            return True
        if not module.install() or not module.check_existence():
            logger.logger.error("%s installation did not complete.", module.NAME)
            return False
    return module.configure()