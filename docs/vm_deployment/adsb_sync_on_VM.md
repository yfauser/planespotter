Steps to create a ADSB-Sync Service VM:
=======================================

On one of the Ubuntu 16.04 LTS VMs do the following:

```shell
sudo apt-get update
sudo apt-get install python-pip python-dev

sudo pip install --upgrade pip
sudo pip install virtualenv
```

Now get the planespotter code from Github and install the necessary Python dependencies for the code in an virtualenv environment:

```shell
cd /home/ubuntu

git clone https://github.com/yfauser/planespotter.git

cd planespotter/
virtualenv adsb-sync
cd adsb-sync/
source bin/activate
pip install -r requirements.txt
```

Create the adsb-sync service config:

```shell
cat << EOF > /home/ubuntu/planespotter/adsb-sync/synchronizer/config/config.ini
[main]
redis_server = localhost
adsb_server_stream = pub-vrs.adsbexchange.com
adsb_port = 32030
adsb_server_poll_url = https://public-api.adsbexchange.com/VirtualRadar/AircraftList.json
adsb_poll_filter = ?fRegS=N
adsb_type = poll
EOF
```

__NOTE:__ In the above config, I asume that the redis service is running on `localhost`. If you deployed redis in a separate VM, please edit the key `redis_server` with the value of your VMs DNS entry or Ip Address.

__NOTE:__ The key `adsb_type` can either be `poll` or `stream`. Stream is preferred to not overload the public adsb esxchange server with API calls. Also, data is more current when using stream. However, the stream version has proven to be problematic for some firewall systems because of its constant stream on a non standard TCP Port.

Finally, we will switch user context and get a root shell to create a Systemd Unit that starts our adsb-sync service every time the VM boots (and initially):

```shell
sudo -H bash
```

```shell
cat << EOF > /etc/systemd/system/adsb-sync.service
[Unit]
Description=adsb-sync
After=network.target
[Unit]
Description=adsb-sync
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/planespotter/adsb-sync/synchronizer
Environment="PATH=/home/ubuntu/planespotter/adsb-sync/bin"
ExecStart=/home/ubuntu/planespotter/adsb-sync/bin/python -u adsb-sync.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
```

```shell
systemctl start adsb-sync
systemctl enable adsb-sync
```
