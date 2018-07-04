Deployment as VMs
=================
Follow the bellow instructions if you want to deploy all Planespotter components on VMs

# Step 1) Prepare the base VMs
In the VM based Model, we will use standard Ubuntu 16.04 LTS VMs.
You can either use one VM per service, so you would have:
- 1x Front-End VM (or more if you want to demonstrate Load-Balancing)
- 1x API App Server VM (or more if you want to demonstrate Load-Balancing)
- 1x Redis VM
- 1x ADSB Sync Service VM
- 1x MySQL Database VM

To reduce the number of VMs its better to collapse some services, in theory everything could easily run in a single VM.
My suggestion, and that's what I'm basing this instructions on is:

- 1x Front-End VM
- 1x API App Server VM
- 1x Redis VM with co-located ADSB Sync Service
- 1x MySQL VM


# Step 2) Create the MySQL Database
Install MySQL and create the Planespotter Database using the instruction in [MySQL_on_VM.md](MySQL_on_VM.md)

Make sure that the VM is resolvable through DNS, in this documentation we will use `mysql.yflab.de`, whenever this fqdn is used, exchange it with your domain and desired hostname.


# Step 3) Create the API App Server
Install the Planespotter App Server using the instructions in [API_Server_on_VM.md](API_Server_on_VM.md)

__NOTE:__ Don't forget to add correct DNS entries to your config files pointing to the service VMs, or populate the `/etc/hosts file` of your VMs. Alternatively, you can also use IPs in the config files.

Make sure that the VM is resolvable through DNS, in this documentation we will use `planespotter-api.yflab.de`, whenever this fqdn is used, exchange it with your domain and desired hostname.

# Step 4) Create the Frontend Server
Install the Planespotter Frontend Server using the instructions in [FE_on_VM.md](FE_on_VM.md)

Make sure that the VM is resolvable through DNS, in this documentation we will use `planespotter.yflab.de`, whenever this fqdn is used, exchange it with your domain and desired hostname.

# Step 5) Create the Redis and ADSB Sync Server
Install the Redis Server using the instructions in [Redis_on_VM.md](Redis_on_VM.md)
On the same VM install the ASDB Sync Service using the instruction in [adsb_sync_on_VM.md](adsb_sync_on_VM.md)

Make sure that the VM is resolvable through DNS, in this documentation we will use `redis.yflab.de`, whenever this fqdn is used, exchange it with your domain and desired hostname.

__That's it, everything should be running now!__