# Adapting kubespray to deploy k8s within Embassy cloud portal

* get latest kubespray
* deploy
* start k8s-galaxy 
* trigger k8s-galaxy workflow execution

after checkout and getting the latest kubespray, recreating some symlinks might be necessary:
* ./<latest kubespray>/extra_playbooks/roles -> ../roles
* ./<latest kubespray>/extra_playbooks/inventory -> ../inventory
* ./<latest kubespray>/contrib/terraform/group_vars -> ../../inventory/group_vars
* ./<latest kubespray>/contrib/terraform/openstack/hosts -> ../terraform.py
* ./<latest kubespray>/contrib/terraform/openstack/group_vars -> ../../../inventory/group_vars
* ./<latest kubespray>/contrib/network-storage/glusterfs/group_vars -> ../../../inventory/group_vars
* ./<latest kubespray>/contrib/network-storage/glusterfs/roles/bootstrap-os -> ../../../../roles/bootstrap-os
* ./kubespray -> <latest kubespray>


## troubleshooting
in case of ssh connection issues check if there are still ssh folders in /tmp lingering
``` bash
rm /tmp/kubespraytest-k8s-*
```
also cleanse known_hosts from bastion public_ip

## to bring up the deployment
```
./up.sh
```
## to destroy the deployment 
use 
``` bash
terraform destroy --force --input=false --state=deployments/deployment-ref-ubuntu/terraform.tfstate
```
