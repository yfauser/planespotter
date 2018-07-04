Steps to create a Planespotter API App Server VM:
=================================================
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
virtualenv app-server
cd app-server/
source bin/activate
cd app
pip install uwsgi Flask-Restless PyMySQL Flask-SQLAlchemy requests redis
```

We now still have to add the right entrypoint for our app in the wsgi app server config, as well as creating the configuration file for the app server:

```shell
cat << EOF > /home/ubuntu/planespotter/app-server/app/wsgi.py
from main import app

if __name__ == "__main__":
    app.run()
EOF
```
```shell
cat << EOF > /home/ubuntu/planespotter/app-server/app/app-server.ini
[uwsgi]
module = wsgi:app
master = true
processes = 5
socket = app-server.sock
chmod-socket = 660
vacuum = true
die-on-term = true
logto = /var/log/uwsgi/%n.log
EOF
```

And we need to populate the Config file that points the API App Server to the Backends and sets some details like used TCP Ports:

```shell
cat << EOF > /home/ubuntu/planespotter/app-server/app/config/config.cfg
DATABASE_URL = 'mysql.yflab.de'
DATABASE_USER = 'planespotter'
DATABASE_PWD = 'VMware1!'
DATABASE = 'planespotter'
REDIS_HOST = 'redis.yflab.de'
REDIS_PORT = '6379'
LISTEN_PORT = '80'
EOF
```

__NOTE:__ You will need to change the config file above to use the right `DATABASE_URL` and `REDIS_HOST` DNS hostnames or IP addresses for your environment.

Finaly, we will switch user context and get a root shell to create a Systemd Unit that starts our App Server everytime the VM boots (and initially):

```shell
sudo -H bash

mkdir -p /var/log/uwsgi
chown -R ubuntu:ubuntu /var/log/uwsgi
```

```shell
cat << EOF > /etc/systemd/system/app-server.service
[Unit]
Description=uWSGI instance to serve app-server
After=network.target
[Unit]
Description=uWSGI instance to serve app-server
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/planespotter/app-server/app
Environment="PATH=/home/ubuntu/planespotter/app-server/bin"
ExecStart=/home/ubuntu/planespotter/app-server/bin/uwsgi --ini app-server.ini
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
```

```shell
systemctl start app-server
systemctl enable app-server
```

The next steps will instruct the NGINX Web-Server to call the App Server for our API Service

```shell
cat << EOF > /etc/nginx/sites-enabled/default
server {
    listen 80;
    server_name default;
    location / {
        include uwsgi_params;
        uwsgi_pass unix:/home/ubuntu/planespotter/app-server/app/app-server.sock;
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

You can now test if you can retrieve data from the MySQL DB through the API Server:

```
curl http://planespotter-api.yflab.de/api/healthcheck
curl http://planespotter-api.yflab.de/api/planes
```
__NOTE:__ Exchange `planespotter-api.yflab.de` with either 127.0.0.1 or the DNS Name or IP of your API Server VM
