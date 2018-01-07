#!/bin/bash

wget http://registry.faa.gov/database/ReleasableAircraft.zip
unzip ReleasableAircraft.zip
rm ReleasableAircraft.zip DEALER.txt DEREG.txt DOCINDEX.txt ENGINE.txt RESERVED.txt
mysql -u root -p < ~/planespotter/db-install/create-planespotter-db.sql
rm MASTER.txt ACFTREF.txt
