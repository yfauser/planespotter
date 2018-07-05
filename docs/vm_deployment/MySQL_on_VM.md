How to prepare a MySQL Database for the Demo
============================================

# Base Installation
See more details here: <https://www.digitalocean.com/community/tutorials/how-to-install-mysql-on-ubuntu-16-04>

1. Install an Ubuntu 16.04 LTS VM
2. Run `sudo apt-get update && sudo apt-get upgrade -y` to update the distro
3. Install mysql-server with `sudo apt-get install mysql-server` (It will also ask you for the new root password)
4. Test if MySQL is running `sudo systemctl status mysql.service`

# Make MySQL available externally

5. Open the file `/etc/mysql/mysql.conf.d/mysqld.cnf` with your favorite editor and comment out the `bind-address = 127.0.0.0` line
6. Restart mysql with `sudo systemctl restart mysql.service`

# Some more housekeeping

7. Install unzip and git with `sudo apt-get install unzip git`

# Create the Database

8. Clone this repo to the MySQL server, `git clone https://github.com/yfauser/planespotter.git`
9. Change the two DB shell scripts to be executable `chmod +x ~/planespotter/db-install/*.sh`
10. Set the evinronment variable for the MySQL root password you used earlier in step 3. This will be used by the DB install scripts in steps 11 and in the cleanup. `export MYSQL_ROOT_PASSWORD=password`

11. Execute the DB creation script `~/planespotter/db-install/create-planespotter-db.sh`

# Cleanup

If you ever want to recreate the database, you can use the DB deletion scrip `~/planespotter/db-install/delete-planespotter-db.sh` to drop the DB, and then recreate the DB starting with step 9.




