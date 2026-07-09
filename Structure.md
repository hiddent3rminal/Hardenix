📁 core 
    🗎 backup.py

        This file handles everything about back, in quick setup hardening , this file satarts first to backup currently running configuration and make a backup folder in "📁 Hardenix Backup"

        Flow :
            Program Starts
                │
                ▼
            Create timestamped backup folder
                │
                ▼
            Loop through all service modules
                │
                ▼
            Check if service exists
                │
                ├── No → Skip
                │
                └── Yes
                        │
                        ▼
                Get configuration paths
                        │
                        ▼
                Copy each file/folder
                        │
                        ▼
            Repeat for next service
                        │
                        ▼
            Backup finished
                        │
                        ▼
            Compress backup folder into ZIP
                        │
                        ▼
            Program ends


    🗎 logger.py

        This file handles everything about logging, from when Hardenix start until the end, it captures and save everything to debug in "📁 logs" folder

        Flow :
            Program starts
                │
                ▼
            Create logs/ directory (if needed)
                │
                ▼
            Create/retrieve the "Hardenix" logger
                │
                ▼
            Set logger level to DEBUG
                │
                ▼
            If no handlers exist:
                │
                ├── Create FileHandler (logs/hardenix.log)
                ├── Set its level to DEBUG
                ├── Create a formatter
                ├── Attach the formatter to the handler
                └── Attach the handler to the logger
                │
                ▼
            Other modules import `logger`
                │
                ▼
            Log messages are written to `logs/hardenix.log`


    🗎 restore.py (Not Implemented yet!)

        This file used to restore backup file  

    🗎 runner.py

        This file handles command that other functions and files need to run, it's created to keep the project modular! 

        Flow :
                                runner.py
                                    │
                                    ▼
                        Function is called
                                    │
                                    ▼
                    Is it a system command?
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
            run_command()                  apply_sysctl(config)
                    │                               │
                    ▼                               ▼
            Execute command              Write sysctl configuration
                    │                               │
                    ▼                               ▼
            Log execution               Save configuration file
                    │                               │
                    ▼                               ▼
            Return result              Reload settings (sysctl --system)
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                        Operation successful?
                                    │
                        ┌───────────┴───────────┐
                        │                       │
                        ▼                       ▼
                Log success             Log exception/error
                        │                       │
                        ▼                       ▼
                Return success           Return failure

    🗎 status.py (Not Implemented yet!)

        This file use to show the Interactive/Summary of server and services status. 




📁 module

    🗎 apache.py
    
    🗎 bind9.py

    🗎 fail2ban.py

    🗎 mysql.py

    🗎 network.py

    🗎 ntp.py

    🗎 openvpn.py

    🗎 samba.py

    🗎 ssh.py

    🗎 swappy

    🗎 timezone.py

    🗎 ufw.py

    🗎 users.py








📁 workflow
    🗎 quick_setup.py

📁 Hardenix_Backup


📁 logs



🗎 main.py

🗎 requirements.txt

🗎 README.md

🗎 .gitignore

🗎 License