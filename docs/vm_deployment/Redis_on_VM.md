Steps to create a Redis Server VM:
==================================
See this article as base reference: https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-redis-on-ubuntu-16-04

On one of the Ubuntu 16.04 LTS VMs do the following:

```shell
sudo apt-get update
sudo apt-get install build-essential tcl
```

Install Redis from source

```shell
cd /tmp
curl -O http://download.redis.io/redis-stable.tar.gz
tar xzvf redis-stable.tar.gz
cd redis-stable
make
make test
sudo make install
sudo mkdir /etc/redis
sudo cp /tmp/redis-stable/redis.conf /etc/redis
```

Now we will configure Redis:

```shell
sudo vim /etc/redis/redis.conf
```

In the file, find the supervised directive.
Currently, this is set to no. Since we are running an operating system that uses the systemd init system,
we can change this to systemd

  `supervised systemd`

Next, find the dir directory. This option specifies the directory that Redis will use to dump persistent data.
We need to pick a location that Redis will have write permission and that isn't viewable by normal users.
We will use the /var/lib/redis directory for this, which we will create in a moment

  `dir /var/lib/redis`

Also comment the line:

  `#bind 127.0.0.1`

and change protected mode to 'no':

  `protected-mode no`

Finaly, we will switch user context and get a root shell to create a Systemd Unit that starts our Redis Server everytime the VM boots (and initially):

```shell
sudo -H bash
```

```shell
cat << EOF > /etc/systemd/system/redis.service
[Unit]
Description=Redis In-Memory Data Store
After=network.target

[Service]
User=redis
Group=redis
ExecStart=/usr/local/bin/redis-server /etc/redis/redis.conf
ExecStop=/usr/local/bin/redis-cli shutdown
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
```

```shell
adduser --system --group --no-create-home redis
mkdir /var/lib/redis
chown redis:redis /var/lib/redis
chmod 770 /var/lib/redis
```

```shell
sudo systemctl start redis
```

Now test if redis is ready using the CLI and enter `ping`

```shell
redis-cli
127.0.0.1:6379> ping
```