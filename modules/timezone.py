from core import runner
from main import clear_screen
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit import prompt
from core import logger
from datetime import datetime



NAME = "timezone"

VERSION = "1.0"

DESCRIPTION = "date and time setup Module"

SUPPORTED_DISTROS = [
    "ubuntu",
    "debian"
]

CONFIG_PATHS = []

SERVICES = []

PACKAGES = []



def check_existence():
    return False

def install():
    pass

def configure():

    while True:

        change_menu = input(f"""
1️⃣ : Change TimeZone
2️⃣ : Chnage TIme/Date Manualy 
3️⃣ : Disable/Enbale NTP 
4️⃣ : Chnage NTP Server
5️⃣ : Sync With NTP Now 

""")

        if change_menu == "1" :
            _change_timezone()
            break
        elif change_menu == "2" :
            _change_time_manually()
            break
        elif change_menu == "3" :
            _change_ntp_status()
            break
        elif change_menu == "4" :
            _change_ntp_server()
            break
        elif change_menu == "5" :
            _sync_ntp()
            break
        else :
            print("Invalid option, try again")
            clear_screen()


def backup():
    pass

def restore():
    pass

def status():

    def _get_status(name):
        result = runner.run_command(["timedatectl", "show", f"--property={name}"])
        return result.stdout.split("=", 1)[1].strip()


    current_timezone = _get_status("Timezone")

    current_time = _get_status("TimeUSec")

    current_ntp = _get_status("NTP")

    current_ntp_sync = _get_status("NTPSynchronized")


    while True:

        status_layout = input(f"""
Your Current TimeZone Is : {current_timezone}
Your Current Time Is : {current_time}
Using NTP : {current_ntp}
NTP Synced With System : {current_ntp_sync}

Are These Settings Correct ? 
Enter n To Change And Enter For Just Skip : """).lower()

        if status_layout == "n":
            configure()
            break
        elif status_layout == "":
            print("Skiping")
            break

        else:
            print("Invalid Input!")
            clear_screen()

            


# all third party functions related to managing timezone 
def _get_timezones():
    result = runner.run_command(["timedatectl", "list-timezones"])
    return result.stdout.splitlines()

def _select_timezone():
    timezones = _get_timezones()
    completer = WordCompleter(timezones,ignore_case=True)
    timezone = prompt("Select Timezone : ", completer=completer)
    return timezone

def _set_timezone(timezone):
    result_timezone = runner.run_command(["timedatectl", "set-timezone", f"{timezone}"])
    if result_timezone.returncode == 0:
        print(f"timezone changed to {timezone}")
        logger.logger.info(f"User timezone chnaged to {timezone}")
    else:
        logger.logger.debug("could not chjange timezone")



# third party functions for manual date and time setup 

def _validate_datetime(date, time):
    try:
        parsed = datetime.strptime(
            f"{date} {time}",
            "%Y-%m-%d %H:%M:%S"
        )

        return (
            parsed.strftime("%Y-%m-%d") == date and
            parsed.strftime("%H:%M:%S") == time
        )

    except ValueError:
        return False

def _change_timezone():

    timezone = _select_timezone()
    if timezone:
        _set_timezone(timezone)

def _change_time_manually(): 

    while True:
        date = input("Enter date (YYYY-MM-DD): ")
        time = input("Enter time (HH:MM:SS): ")

        if _validate_datetime(date, time):
            break

        print("❌ Invalid date or time format!")


    result_ntp = runner.run_command(
        ["timedatectl", "set-ntp", "false"]
    )

    if result_ntp.returncode != 0:
        print("❌ Could not disable NTP")
        return


    result_time = runner.run_command(
        ["timedatectl", "set-time", f"{date} {time}"]
    )


    if result_time.returncode == 0:
        print("✅ System date/time changed successfully")
        logger.logger.info(
            f"System date/time changed to {date} {time}"
        )
    else:
        print("❌ Failed to change system time")
        logger.logger.error(
            "Failed to change system time"
        )

    

def _change_ntp_status():

    result = runner.run_command(["timedatectl", "show", "--property=NTP"])

    

    if result.returncode != 0:
        logger.logger.error("could not get ntp status maybe does not support !")
        return 
    else:
        ntp_status = result.stdout.split("=", 1)[1].strip()
        if ntp_status == "yes":
            chnage_status = input("Your NTP Is On Would You Turn It Off ? press y : ").lower()
            if chnage_status == "y":
                result1 = runner.run_command(["timedatectl", "set-ntp", "false"])
                if result1.returncode != 0:
                    logger.logger.debug("Could not to turn of ntp !")
                else:
                    logger.logger.info("ntp disabled by user!")
                    print("NTP Successfuly Disabled ❌")
            else:
                pass



        elif ntp_status == "no":
            chnage_status1 = input("Your NTP IS Off Would You Turn It On ? press y : ").lower()
            if chnage_status1 == "y":
                result2 = runner.run_command(["timedatectl", "set-ntp", "true"])
                if result2.returncode != 0 :
                    logger.logger.debug("Could not turn on ntp !")

                else:
                    logger.logger.debug("ntp enabled by user !")
                    print("NTP Successfuly Enabled ✅")

            else:
                pass



def _detect_ntp_service():

    services = [
        "systemd-timesyncd",
        "chrony",
        "ntp",
        "ntpd"
    ]

    for service in services:
        result = runner.run_command(
            ["systemctl", "is-active", service]
        )

        if result.returncode == 0 and result.stdout.strip() == "active":
            return service

    return None


# ntp config files 

TIMESYNCD_CONFIG = "/etc/systemd/timesyncd.conf"
    
def _get_current_ntp_server():
    result = runner.run_command(
        ["timedatectl", "show-timesync", "--property=ServerName"]
    )

    if result.returncode != 0:
        logger.logger.error("Could not get NTP server")
        return None

    return result.stdout.split("=", 1)[1].strip()

    
def _change_ntp_server():

    service = _detect_ntp_service()
    if service != "systemd-timesyncd":
        print(f"Unsopported NTP service {service}")
        return

    current = _get_current_ntp_server()
    if current:
        print(f"Current NTP server : {current}")
    else:
        print(f"Current NTP Server : Default/Unknown")

    new_server = input("Enter new NTP server: ").strip()

    if not new_server:
        return


    with open(TIMESYNCD_CONFIG , "r", encoding="utf-8") as file:
        lines = file.readlines()


    found = False
    new_lines = []

    for line in lines:
        if (not found) and (line.strip().startswith("NTP=") or line.strip().startswith("#NTP=")) :
            new_lines.append(f"NTP={new_server}\n")
            found = True
        else:
            new_lines.append(line)


    if not found:
        new_lines.append(f"\nNTP={new_server}\n")

    
    with open(TIMESYNCD_CONFIG , "w", encoding="utf-8") as file:
        file.writelines(new_lines)


    restart = runner.run_command(
        ["systemctl", "restart", "systemd-timesyncd"]
    )


    if restart.returncode == 0:
        print("✅ NTP server changed successfully")
        logger.logger.info(
            f"NTP server changed to {new_server}"
        )
    else:
        print("❌ Failed to restart systemd-timesyncd")

def _sync_ntp():

    service = _detect_ntp_service()

    if service != "systemd-timesyncd":
        print("Unsupported NTP service")
        return


    restart = runner.run_command(
        ["systemctl","restart","systemd-timesyncd"]
    )


    if restart.returncode != 0:
        print("❌ Failed to restart time sync service")
        return


    status = runner.run_command(
        [
            "timedatectl",
            "show",
            "--property=NTPSynchronized"
        ]
    )


    print(status.stdout)