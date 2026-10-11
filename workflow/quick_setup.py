# workflow/quick_setup.py


from modules import network
from modules import timezone

from core import logger
from core import backup
from core import status



def run_step(name, function):
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


    steps = [

        (
            "Backup",
            backup.create_backup
        ),

        (
            "Timezone",
            timezone.configure
        ),

        (
            "Network",
            network.configure
        ),
    ]

    print(
        "SSH hardening, Fail2Ban, and firewall configuration are not implemented "
        "and will be skipped."
    )
    # TODO: Add these steps only after their modules can verify effective system state.
    logger.logger.warning(
        "Unsupported hardening features skipped: SSH, Fail2Ban, and firewall."
    )

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