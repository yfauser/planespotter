#!/bin/bash

cd ~/planespotter/db-install/
wget http://registry.faa.gov/database/ReleasableAircraft.zip
unzip ReleasableAircraft.zip
rm ReleasableAircraft.zip DEALER.txt DEREG.txt DOCINDEX.txt ENGINE.txt RESERVED.txt
mysql --user=root --password=$MYSQL_ROOT_PASSWORD < create-planespotter-db.sql
rm MASTER.txt ACFTREF.txt
