🩸This is a program to graph the Libre Freestyle readings in realtime. If it goes under 4.0 mmol/L it will sound an alarm and speak text stating your in Hypo. You may change this in the code to suit your needs. Only works in English however you can change this if you want. When run for the first time you will have to enter your username and password from your Libre Freestyle app. Then it will load the Matplotlib graph and give time and readings for 12 hours or so. If you have any questions just comment me on Redit.

** Added a MySQL option where you create a mysql_config.json in your documents folder in your Users directory location not Onedrive like this

{  
        "host":"hostname",
        "user":"username",
        "password":"password123",
        "database":"databasename"
}

And simply run the program later you can use the MySQL data in other programs to manipulate them how ever you wish.

Just one thing it interferes with the Screen Saver in Windows 10 when if you want I have another project which solves that problem.

I use a version for Linux where it is more stable and my computer reboots even after a power failure where this is usefull. Don`t loose access to it unlike my newer computers that power off after a long delay. I have a UPS but for only 10 minutes over that I am screwed. As for running the same Python code for the nograph.py and haveing all .json files found in the /home/<username>/ directory compared to the Windows installation.

Will add an email option if available in a future version which will send an email every hour to where ever you wish. This will be used only in the Linux version I will call the program nographlinux.py. I will keep you informed of any changes.
