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


NOTE:
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
Now we can deploy the Planespotter MySQL Database as a K8s Pod. Please take note of the config section, this is where the MySQL startup script will check if there is an existing Database in the persisten volume. This means that if you deleted the MySQL Pod, but kept the persistent volume, the time consuming download of the Data from the FAA Web-Site will be skipped and the existing Data will be used.

