Planespotter App
================
Welcome to the home of the Planespotter Cloud Native Demo App.

I developed this App to demonstrate various networking capabilities of VMware NSX in vSphere, Kubernetes and Cloud Foundry environments. If you are curious to see what a VMware NSX Demo with Planespotter looks like, you can watch this Presentation at Network Field Day 17:

[![NFD17 Planespotter Demo](https://github.com/yfauser/planespotter/blob/master/docs/pics/NFD-Screenshot.png)](https://youtu.be/SN4eJk3C7uc "NFD17 Planespotter Demo")

Planespotter is composed of a MySQL DB that holds Aircraft registration data from the FAA. You can search through the data in the DB through an API App Server written in Python using Flask. The API App Server is also retrieving data from a Redis in memory cache that contains data from aircrafts that are currently airborne. There's a service written in Python that retrieves the Data about airborne aircrafts and pushes that data into Redis. Finally there is a Frontend written with Python Flask and using Bootstrap.

There's no specific mandatory way to deploy Planespotter. It can be deployed in various ways ranging from all in VMs, to Kubernetes, Cloud Foundry, etc.

Deployment Instructions:
========================
If you are planing to deploy the application using a VM only approach, follow the [VM based deployment instructions](https://github.com/yfauser/planespotter/tree/master/docs/vm_deployment/README.md).

If you want to have a deployment where everything including the MySQL DB is deployed in Kubernetes, you can follow the [full deployment in Kubernetes instructions](https://github.com/yfauser/planespotter/tree/master/docs/all_k8s_deployment/README.md).

Another option is to still deploy the MySQL DB using a VM based model, but keep everything else in Kubernetes. Follow the [VM and Kubernetes Deployment instructions](https://github.com/yfauser/planespotter/tree/master/docs/vm_k8s_deployment/README.md) for this.

If you want to mix VMs, Kubernetes and Cloud Foundry, follow the [VM, K8s, CF deployment instructions](https://github.com/yfauser/planespotter/tree/master/docs/vm_k8s_cf_deployment/README.md).

Communication Matrix:
=====================
One of the goals of the Planespotter app is to demonstrate micro-segmentation policies in Kubernetes, Cloud Foundry, vSphere with NSX, etc. Therefore the App is build with this in mind and uses quick timeouts to show the impact of firewall rule changes and includes a 'healtcheck' function that reports back communication issues between the 'microservices' of the app.

Here's the Communication Matrix of the component amongst each other and to the external world:

| Component / Source     | Component / Destination       | Dest Port | Notes                               |
|:-----------------------|:------------------------------|:----------|:------------------------------------|
| Ext. Clients / Browser | Planespotter Frontend         | TCP/80    |                                     |
| Ext. Clients / Browser | www.airport-data.com          | TCP/80    | Display Aircraft Thumbnail picture  |
| Planespotter Frontend  | Planespotter API/APP          | TCP/80    | The listening port is configurable  |
| Planespotter API/APP   | Planespotter MySQL	         | TCP/3306  | 									   |
| Planespotter API/APP   | Planespotter Redis	         | TCP/6379  | 									   |
| Planespotter API/APP   | www.airport-data.com          | TCP/80    | Find Aircraft Thumbnail pictures    |
| Planespotter API/APP   | public-api.adsbexchange.com   | TCP/443   | Retrieves latest Aircraft position  |
| ADSB-Sync       		 | www.airport-data.com          | TCP/443   | Retr. Acft. Airbone stat. in poll   |
| ADSB-Sync       		 | www.airport-data.com          | TCP/32030 | Retr. Acft. Airbone stat. in stream |
| ADSB-Sync       		 | Planespotter Redis            | TCP/6379  | 									   |


Contributing & Feedback:
========================
I welcome any contributions through pull requests, direct communication, etc.
If you run into issues and need help, please open Github issues so that I can track this better and for other people to learn about open issues and potential workarounds.

License:
========
Copyright © 2018 Yves Fauser. All Rights Reserved.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions
of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.

Acknowledgments
===============
I integrated a couple of ideas on how to deploy the App from https://github.com/nvpnathan, https://github.com/puckpuck and https://github.com/howardyoo. Thanks!

