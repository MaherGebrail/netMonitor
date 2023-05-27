# netMonitor

netMonitor is a python app that works as a service in linux to monitor the network traffic by apps.

**install.sh** .. it's rule is to copy the app files to **/opt/netMonitor** and run the app as a service.

**netMonitor.py** .. The app itself, which runs a loop to get net traffic running and print the result to a report, so you can see what's happening on your pc.

**config_file.json** .. The settings that the app needs to run as it should, their are comments with every option so it clear for easily manage.

**startNetMonitor.service** .. the service file of the app.
