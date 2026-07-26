# workflow/quick_setup.py


from modules import ssh
from modules import ufw
from modules import fail2ban
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


        if result is False:

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
        4. Harden SSH
        5. Configure Fail2Ban
        6. Configure Firewall
        7. Show final status

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

        (
            "SSH",
            ssh.configure
        ),

        (
            "Fail2Ban",
            fail2ban.configure
        ),

        (
            "UFW Firewall",
            ufw.configure
        ),

    ]



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

        status.show_summary()


    except Exception as error:

        logger.logger.exception(
            f"Status check failed: {error}"
        )


    logger.logger.info(
        "========== Quick Basic Hardening Completed Successfully =========="
    )


    return True