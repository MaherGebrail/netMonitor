#!/usr/bin/env bash


if [ $USER != "root" ] ;then 
    echo "This script needs root Permission .. run it as sudo to work properly"
    exit 0
fi


APP_DIR="/opt/netMonitor"

mkdir $APP_DIR

cp  netMonitor.py config_file.json $APP_DIR
chmod 550 $APP_DIR/netMonitor.py $APP_DIR/config_file.json

cp  startNetMonitor.service /etc/systemd/system/
chmod 550 /etc/systemd/system/startNetMonitor.service

sudo systemctl daemon-reload 

sudo systemctl start startNetMonitor
sudo systemctl enable startNetMonitor
