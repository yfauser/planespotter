Full deployment in Kubernetes
=============================
Follow the bellow instructions if you want to deploy all Planespotter components in Kubernetes only

Step 1) Prepare your K8s environment to support persistent volumes
------------------------------------------------------------------
The MySQL Database will be deployed in Kubernetes using a statefulset and the data will be written into a persistent volume. With that, you will only need to create your database once and keep the data in a persistent volume.
There are [various PV types you can use](https://kubernetes.io/docs/concepts/storage/persistent-volumes/). I tested with the [vSphere PV Drivers](https://vmware.github.io/vsphere-storage-for-kubernetes/documentation/).

As a first step, make sure your K8s deployment support persistent volumes. If you want to use the vSphere drivers as I do, you can follow the [Enabling vSphere Cloud Provider with automation script](https://github.com/vmware/kubernetes/blob/enable-vcp-uxi/README.md) instructions on VMware Github site.

Step 2) Create a new Namespace for the Planespotter App and create the persistent volume
----------------------------------------------------------------------------------------
Create a new namespace and set your Kubernetes CLI to use this Namespace by default

```shell
kubectl create ns planespotter
kubectl config set-context kubernetes-admin@kubernetes --namespace planespotter
```

If you haven't done this already, create a storage class and add it to your Kubernetes environment:


```yaml
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: thin-disk
provisioner: kubernetes.io/vsphere-volume
parameters:
    diskformat: thin
```
[`storage_class.yaml`](../../kubernetes/storage_class.yaml)


__NOTE:__
The above storage class has a vSphere provider specific parameter, your actual storage class might differ from the above

```shell
kubectl create -f storage_class.yaml
```

We will use dynamic volume provisioning using a persistent volume claim. Alternatively you could create a static volume and map it to the MySQL Pod.

```yaml
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: mysql-claim
  namespace: planespotter
  annotations:
    volume.beta.kubernetes.io/storage-class: thin-disk
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 2Gi
```
[`mysql_claim.yaml`](../../kubernetes/mysql_claim.yaml)

```shell
kubectl create -f mysql_claim.yaml
```

Review the now created persistent volume:
```shell
▶ kubectl get pvc
NAME          STATUS    VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
mysql-claim   Bound     pvc-2784ef8a-7ec2-11e8-8a7b-0050569aca4b   2Gi        RWO            thin-disk      1m
```

Step 3) Deploy the MySQL Pod
----------------------------
Now we can deploy the Planespotter MySQL Database as a K8s Pod. Please take note of the config section, this is where the MySQL startup script will check if there is an existing Database in the persisten volume. This means that if you deleted the MySQL Pod, but kept the persistent volume, the time consuming download of the Data from the FAA Web-Site will be skipped and the existing Data will be used.

```yaml
---
apiVersion: v1
kind: Service
metadata:
  name: mysql
  namespace: planespotter
  labels:
    app: mysql
spec:
  ports:
  - port: 3306
    name: mysql
  clusterIP: None
  selector:
    app: mysql
---
apiVersion: apps/v1beta1
kind: StatefulSet
metadata:
  name: mysql
  namespace: planespotter
spec:
  serviceName: mysql
  replicas: 1
  template:
    metadata:
      labels:
        app: mysql
    spec:
      terminationGracePeriodSeconds: 10
      containers:
      - name: mysql
        image: mysql:5.6
        env:
          # Use secret in real usage
        - name: MYSQL_ROOT_PASSWORD
          value: password
        ports:
        - containerPort: 3306
          name: mysql
        volumeMounts:
        - name: mysql-vol
          mountPath: /var/lib/mysql
        - name: mysql-config
          mountPath: /bin/planespotter-install.sh
          subPath: planespotter-install.sh
        - name: mysql-start
          mountPath: /bin/mysql-start.sh
          subPath: mysql-start.sh
        command: ["/bin/mysql-start.sh"]
      volumes:
      - name: mysql-vol
        persistentVolumeClaim:
          claimName: mysql-claim
      - name: mysql-config
        configMap:
          defaultMode: 0700
          name: mysql-config-map
      - name: mysql-start
        configMap:
          defaultMode: 0700
          name: mysql-start-map
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: mysql-config-map
  namespace: planespotter
data:
  planespotter-install.sh: |
    #!/bin/sh
    # sleep while mysql is starting up
    while [ -z "$ALIVE" ] || [ "$ALIVE" != 'mysqld is alive' ]
    do
      echo "waiting for mysql..."
      sleep 3
      ALIVE=`mysqladmin ping --user=root --password=$MYSQL_ROOT_PASSWORD`
      echo "status: $ALIVE"
    done
    echo "MYSQL is alive, checking database..."
    DBEXIST=`mysql --user=root --password=$MYSQL_ROOT_PASSWORD -e 'show databases;' | grep planespotter`
    if ! [ -z "$DBEXIST" ]
    then
      echo "planespotter db already installed."
    else
      echo "------- MYSQL DATABASE SETUP -------"
      echo "updating apt-get..."
      apt-get update
      echo "apt-get installing curl..."
      apt-get --assume-yes install curl
      apt-get --assume-yes install wget
      apt-get --assume-yes install unzip
      echo "downloading planespotter scripts..."
      mkdir ~/planespotter
      mkdir ~/planespotter/db-install
      cd ~/planespotter/db-install
      curl -L -o create-planespotter-db.sh https://github.com/yfauser/planespotter/raw/master/db-install/create-planespotter-db.sh
      curl -L -o create-planespotter-db.sql https://github.com/yfauser/planespotter/raw/master/db-install/create-planespotter-db.sql
      curl -L -o delete-planespotter-db.sh https://github.com/yfauser/planespotter/raw/master/db-install/delete-planespotter-db.sh
      curl -L -o delete-planespotter-db.sql https://github.com/yfauser/planespotter/raw/master/db-install/delete-planespotter-db.sql
      echo "creating a new planespotter db"
      chmod +x create-planespotter-db.sh
      ./create-planespotter-db.sh
    fi
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: mysql-start-map
  namespace: planespotter
data:
  mysql-start.sh: |
    #!/bin/sh
    echo "starting planespotter-installer in background"
    /bin/planespotter-install.sh &
    echo "starting mysqld.."
    /entrypoint.sh mysqld
```
[`mysql_pod.yaml`](../../kubernetes/mysql_pod.yaml)

```shell
kubectl create -f mysql_pod.yaml
```

Step 4) Deploy the App-Server Pod
---------------------------------
To deploy the API App Server, create the following yaml spec and deploy it:

```yaml
apiVersion: apps/v1beta2
kind: Deployment
metadata:
  name: planespotter-app
  namespace: planespotter
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
  namespace: planespotter
data:
  config.cfg: |
    DATABASE_URL = 'mysql'
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
  namespace: planespotter
  labels:
    app: planespotter-svc
spec:
  ports:
    # the port that this service should serve on
    - port: 80
  selector:
    app: planespotter-app
```
[`app-server-deployment_all_k8s.yaml`](../../kubernetes/app-server-deployment_all_k8s.yaml)

```shell
kubectl create -f app-server-deployment_all_k8s.yaml
```

Step 5) Deploy the Frontend
---------------------------
Now, deploy the frontend using the following yaml spec:

```yaml
---
apiVersion: apps/v1beta1
kind: Deployment
metadata:
  name: planespotter-frontend
  namespace: planespotter
  labels:
    app: planespotter-frontend
    tier: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: planespotter-frontend
  template:
    metadata:
      labels:
        app: planespotter-frontend
        tier: frontend
    spec:
      containers:
      - name: planespotter-fe
        image: yfauser/planespotter-frontend:b0a8b3186c3c18fd23632cf45ff7504b23e7c5b9
        imagePullPolicy: IfNotPresent
        env:
        - name: PLANESPOTTER_API_ENDPOINT
          value: planespotter-svc
---
apiVersion: v1
kind: Service
metadata:
  name: planespotter-frontend
  namespace: planespotter
  labels:
    app: planespotter-frontend
spec:
  ports:
    # the port that this service should serve on
    - port: 80
  selector:
    app: planespotter-frontend
---
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: planespotter-frontend
  namespace: planespotter
spec:
  rules:
  - host: planespotter.demo.yves.local
    http:
      paths:
      - backend:
          serviceName: planespotter-frontend
          servicePort: 80
```
[`frontend-deployment_all_k8s.yaml`](../../kubernetes/frontend-deployment_all_k8s.yaml)

__NOTE:__
You obviously need to adapt the hostname in the Ingress spec to reflect your domain name. So change `- host: planespotter.demo.yves.local` to whatever your desired fqdn is.

```shell
kubectl create -f frontend-deployment_all_k8s.yaml
```

You should now be able to browse to the FQDN you used and get back the Planespotter Web-Pages. You should be able to browse through the Aircraft registry, but you should not yet see any airborne aircrafts, as we haven't deployed the ADSB Sync Service and the Redis in-memory DB/Cache yet

Step 6) Deploy Redis and the ADSB Sync Service
----------------------------------------------
To deploy the redis cache and the ADSB Sync service, you can use the following yaml spec:
```yaml
---
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: redis-server
  namespace: planespotter
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
  namespace: planespotter
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
  namespace: planespotter
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
  namespace: planespotter
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


Optional Step 7) Deploy a K8s network policy to secure the Planespotter app
---------------------------------------------------------------------------
You can apply a micro-segmentation poliy for the Planespotter app with the following K8s Network Policy Spec:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: planespotter
spec:
  podSelector: {}
  policyTypes:
  - Ingress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: planespotter-ing-to-fe
  namespace: planespotter
spec:
  podSelector:
    matchLabels:
      app: planespotter-frontend
  policyTypes:
  - Ingress
  ingress:
    - from:
      - ipBlock:
          cidr: 100.64.160.11/32
      ports:
      - protocol: TCP
        port: 80
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: planespotter-fe-to-app
  namespace: planespotter
spec:
  podSelector:
    matchLabels:
      app: planespotter-app
  policyTypes:
  - Ingress
  ingress:
    - from:
      - podSelector:
          matchLabels:
            app: planespotter-frontend
      ports:
      - protocol: TCP
        port: 80
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: planespotter-app-to-redis
  namespace: planespotter
spec:
  podSelector:
    matchLabels:
      app: redis-server
  policyTypes:
  - Ingress
  ingress:
    - from:
      - podSelector:
          matchLabels:
            app: planespotter-app
      ports:
      - protocol: TCP
        port: 6379
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: planespotter-adsb-to-redis
  namespace: planespotter
spec:
  podSelector:
    matchLabels:
      app: redis-server
  policyTypes:
  - Ingress
  ingress:
    - from:
      - podSelector:
          matchLabels:
            app: adsb-sync
      ports:
      - protocol: TCP
        port: 6379
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: mysql
  namespace: planespotter
spec:
  podSelector:
    matchLabels:
      app: mysql
  policyTypes:
  - Ingress
  ingress:
    - from:
      - podSelector:
          matchLabels:
            app: planespotter-app
      ports:
      - protocol: TCP
        port: 3306

```
[`network-policy.yaml`](../../kubernetes/network-policy.yaml)

__NOTE:__ The Ingress source IP `cidr: 100.64.160.11/32` in the above example will be different in your environment. If you are using the VMware NSX Integration with Kubernetes, you can find the Ingress source IP using `kubectl get ingress <your_fe_ingress_name> -o yaml`

```shell
▶ kubectl get ingress planespotter-frontend -o yaml
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  annotations:
    ncp/internal_ip_for_policy: 100.64.160.11
  creationTimestamp: 2018-07-03T14:55:51Z
  generation: 1
  name: planespotter-frontend
  namespace: planespotter
  resourceVersion: "3260531"
  selfLink: /apis/extensions/v1beta1/namespaces/planespotter/ingresses/planespotter-frontend
  uid: 2dfe8744-7ed1-11e8-8a7b-0050569aca4b
spec:
  rules:
  - host: planespotter.demo.yves.local
    http:
      paths:
      - backend:
          serviceName: planespotter-frontend
          servicePort: 80
status:
  loadBalancer:
    ingress:
    - ip: 10.114.209.201
    - ip: 100.64.160.11
```

The internal Ingress source IP can be found in the annotations section:

```yaml
metadata:
  annotations:
    ncp/internal_ip_for_policy: 100.64.160.11
```

When using other ingress controllers, like NGINX, that run as a Pod themselves, you can simply change the first policy to use a namespace/Pod selector instead of an ipBlock.

Cleanup
-------
If you want to delete everything including the volume holding your database, you can simply delete the complete namespace and change back the Kubectl CLI to use the default namespace:

```shell
kubectl delete ns planespotter
kubectl config set-context kubernetes-admin@kubernetes --namespace default
```

Alternatively, you can remove all the Deployments, Config Maps and Staeful set and keep your database persistent volume for later use:

```shell
kubectl delete -f redis_and_adsb_sync_all_k8s.yaml
kubectl delete -f frontend-deployment_all_k8s.yaml
kubectl delete -f app-server-deployment_all_k8s.yaml
kubectl delete -f mysql_pod.yaml
```
