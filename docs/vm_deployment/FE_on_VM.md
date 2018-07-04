Steps to create a Planespotter Frontent Server VM:
==================================================
See this article as base reference: https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-uwsgi-and-nginx-on-ubuntu-16-04

On one of the Ubuntu 16.04 LTS VMs do the following:

```shell
sudo apt-get update
sudo apt-get install python-pip python-dev nginx

sudo pip install --upgrade pip
sudo pip install virtualenv
```

Now get the planespotter code from Github and install the necessary Python dependencies for the code in an virtualenv environment:

```shell
git clone https://github.com/yfauser/planespotter.git

cd planespotter/
virtualenv frontend
cd frontend/
source bin/activate
cd app
pip install -r requirements.txt
pip install uwsgi
```

We now still have to add the right entrypoint for our app in the wsgiserver config, as well as creating the configuration file for the server:

```shell
cat << EOF > /home/ubuntu/planespotter/frontend/app/wsgi.py
from main import app

if __name__ == "__main__":
    app.run()
EOF
```

```shell
cat << EOF > /home/ubuntu/planespotter/frontend/app/frontend.ini
[uwsgi]
module = wsgi:app
master = true
processes = 5
socket = frontend.sock
chmod-socket = 660
vacuum = true
die-on-term = true
logto = /var/log/uwsgi/%n.log
env = PLANESPOTTER_API_ENDPOINT=planespotter-api.yflab.de
# env = TIMEOUT_REG=5
# env = TIMEOUT_OTHER=5
EOF
```

__NOTE:__ You will need to change the config file above to use the right `PLANESPOTTER_API_ENDPOINT` DNS hostnames or IP addresses to point to the Planespotter API Server you created earlier. If you changed the TCP Port used by the API Server, you can simply add the TCP Port to the end of the fqdn, e.g. `PLANESPOTTER_API_ENDPOINT=planespotter-api.yflab.de:8080`.

The two other commented env variable in the config are for the timeouts, `TIMEOUT_REG` and `TIMEOUT_OTHER`. 5 seconds should be ok, but you can turn those timeouts up if you are in Lab environments with very bad internet connectivity and run into timeouts retrieving data from adsb exchange and the airport-data server (Pictures of Planes).

Finaly, we will switch user context and get a root shell to create a Systemd Unit that starts our Frontend Server everytime the VM boots (and initially):

```shell
sudo -H bash

mkdir -p /var/log/uwsgi
chown -R ubuntu:ubuntu /var/log/uwsgi
```

```shell
cat << EOF > /etc/systemd/system/frontend.service
[Unit]
Description=uWSGI instance to serve frontend
After=network.target
[Unit]
Description=uWSGI instance to serve frontend
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/planespotter/frontend/app
Environment="PATH=/home/ubuntu/planespotter/frontend/bin;PLANESPOTTER_API_ENDPOINT=planespotter-api"
ExecStart=/home/ubuntu/planespotter/frontend/bin/uwsgi --ini frontend.ini
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
```

```shell
systemctl start frontend
systemctl enable frontend
```

The next steps will instruct the NGINX Web-Server to call the uswgi server

```shell
cat << EOF > /etc/nginx/sites-enabled/default
server {
    listen 80;
    server_name default;
    location / {
        include uwsgi_params;
        uwsgi_pass unix:/home/ubuntu/planespotter/frontend/app/frontend.sock;
    }
}
EOF
```
```shell
systemctl restart nginx
```

And finally we will instruct Ufw (IPTables) to allow Web port ingress:

```shell
ufw allow 'Nginx Full'
```

You should now be able to browse to the FE IP or DNS Name and retrieve Data from the MySQL Database.