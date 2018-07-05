Mixed deployment VM, Cloud Foundry & Kubernetes
===============================================
Follow the bellow instructions if you want to deploy the MySQL Database as a VM, the planespotter Frontend in Cloud Foundry, and all other Planespotter components in Kubernetes

# Step 1) Prepare the MySQL base VM
Deploy one standard Ubuntu 16.04 LTS VM.

Simply follow the Steps in [../vm_deployment/MySQL_on_VM.md](../vm_deployment/MySQL_on_VM.md) to create the MySQL VM and the Planespotter DB.

Make sure that the VM is resolvable through DNS, in this documentation we will use `mysql.yves.local`. Whenever this fqdn is used, exchange it with your domain and desired hostname.

# Step 2) Create a new Namespace for the Planespotter App
Create a new namespace and set your Kubernetes CLI to use this Namespace by default

```shell
kubectl create ns planespotter
kubectl config set-context kubernetes-admin@kubernetes --namespace planespotter
```

# Step 3) Deploy the App-Server Pod
To deploy the API App Server, create the following yaml spec and deploy it:

```yaml
apiVersion: apps/v1beta2
kind: Deployment
metadata:
  name: planespotter-app
  labels:
    app: planespotter
    tier: app-tier
spec:
  replicas: 2
  selector:
    matchLabels:
      app: planespotter-app
  template:
    metadata:
      labels:
        app: planespotter-app
    spec:
      containers:
      - name: planespotter
        image: yfauser/planespotter-app-server:1508888202fc85246248c0892c0d27dda34de8e1
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 80
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
      volumes:
        - name: config-volume
          configMap:
            name: planespotter-app-cfg
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: planespotter-app-cfg
data:
  config.cfg: |
    DATABASE_URL = 'mysql.yves.local'
    DATABASE_USER = 'planespotter'
    DATABASE_PWD = 'VMware1!'
    DATABASE = 'planespotter'
    REDIS_HOST = 'redis-server'
    REDIS_PORT = '6379'
    LISTEN_PORT = 80
---
apiVersion: v1
kind: Service
metadata:
  name: planespotter-svc
  labels:
    app: planespotter-svc
spec:
  ports:
    # the port that this service should serve on
    - port: 80
  selector:
    app: planespotter-app
---
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: planespotter-api
spec:
  rules:
  - host: planespotter-api.demo.yves.local
    http:
      paths:
      - backend:
          serviceName: planespotter-svc
          servicePort: 80
```
[`app-server-deployment_vm_cf_k8s.yaml`](../../kubernetes/app-server-deployment_vm_cf_k8s.yaml)

```shell
kubectl create -f app-server-deployment_vm_cf_k8s.yaml
```

__NOTE:__
You need to adapt the `DATABASE_URL` in the ConfigMap to reflect your domain name. So change `DATABASE_URL = 'mysql.yves.local'` to whatever your desired fqdn is.


# Step 4) Deploy the Frontend
Download the Planspotter code to the workstation you are doing the `cf push` from, e.g. by using `git clone https://github.com/yfauser/planespotter.git`

Create a CF Org and Space to hold the Planespotter Frontend

```shell
cf create-org planespotter
cf target -o "planespotter"
cf create-space planespotter
cf target -o "planespotter" -s "planespotter"
```

Now go to the Planespotter Frontend Code:
```shell
cd ~/planespotter/frontend/app
```

Edit the manifest.yaml file and exchange the environment variables `PLANESPOTTER_API_ENDPOINT` value with the fqdn you gave to the Planespotter API/App service in Step 3.

```yaml
---
applications:
- name: planespotter
  memory: 512M
  instances: 1
  buildpack: python_buildpack
  env:
    PLANESPOTTER_API_ENDPOINT: planespotter-api.demo.yves.local
```

After this change, simply to the `cf push` in the directory that holds the `manifest.yml`file.

```shell
cf push
```

After the deployment succeeds, you should now be able to browse to the FQDN you used and get back the Planespotter Web-Pages. You should be able to browse through the Aircraft registry, but you should not yet see any airborne aircrafts, as we haven't deployed the ADSB Sync Service and the Redis in-memory DB/Cache yet

_Optional:_ Scale up the number of Frontend AIs that serve the Frontend:

```shell
cf scale planespotter -i 4
```

# Step 5) Deploy Redis and the ADSB Sync Service
To deploy the redis cache and the ADSB Sync service, you can use the following yaml spec:
```yaml
---
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: redis-server
spec:
  replicas: 1
  template:
    metadata:
      labels:
        app: redis-server
        tier: backend
    spec:
      containers:
      - name: redis-server
        image: redis
        ports:
        - containerPort: 6379
---
apiVersion: v1
kind: Service
metadata:
  name: redis-server
  labels:
    app: redis-server
    tier: backend
spec:
  ports:
  - port: 6379
  selector:
    app: redis-server
    tier: backend
---
apiVersion: apps/v1beta1
kind: Deployment
metadata:
  name: adsb-sync
  labels:
    app: adsb-sync
    tier: data-sync
spec:
  replicas: 1
  selector:
    matchLabels:
      app: adsb-sync
  template:
    metadata:
      labels:
        app: adsb-sync
    spec:
      containers:
      - name: adsb-sync
        image: yfauser/adsb-sync:1d791ea6e96eb50adb15e773d1d783f511618c97
        imagePullPolicy: IfNotPresent
        volumeMounts:
        - name: config-volume
          mountPath: /usr/src/app/config
      volumes:
        - name: config-volume
          configMap:
            name: adsb-sync-cfg
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: adsb-sync-cfg
data:
  config.ini: |
    [main]
    redis_server = redis-server
    adsb_server_poll_url = https://public-api.adsbexchange.com/VirtualRadar/AircraftList.json
    adsb_poll_filter = ?fRegS=N
    adsb_type = poll
```
[`redis_and_adsb_sync_all_k8s.yaml`](../../kubernetes/redis_and_adsb_sync_all_k8s.yaml)


```shell
kubectl create -f redis_and_adsb_sync_all_k8s.yaml
```

__That's it, Planespotter should be all up and running now!!__

