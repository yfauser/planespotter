How to prepare a MySQL Database for the Demo
============================================

# Base Installation
See more details here: <https://www.digitalocean.com/community/tutorials/how-to-install-mysql-on-ubuntu-16-04>

1. Install an Ubuntu 16.04 LTS VM and patch it into an NSX-T Logical Switch, so that NSX-T sees the VM in its inventory.
2. Run `sudo apt-get update && sudo apt-get upgrade -y` to update the distro
3. Install mysql-server with `sudo apt-get install mysql-server` (It will also ask you for the new root password)
4. Test if MySQL is running `systemctl status mysql.service`

# Make MySQL available externally

5. Open the file `/etc/mysql/mysql.conf.d/mysqld.cnf` with your favorite editor and comment out the `bind-address		= 127.0.0.1` line
6. Restart mysql with `systemctl restart mysql.service`

# Some more housekeeping

7. Install unzip and git with ´sudo apt-get install unzip git´






