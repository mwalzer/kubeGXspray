# Adapting kubespray to deploy k8s within Embassy cloud portal

* get latest kubespray
* deploy
* start k8s-galaxy
* trigger k8s-galaxy workflow execution

after checkout and getting the latest kubespray, recreating some symlinks might be necessary:
* `./<latest kubespray>/extra_playbooks/roles -> ../roles`
* `./<latest kubespray>/extra_playbooks/inventory -> ../inventory`
* `./<latest kubespray>/contrib/terraform/group_vars -> ../../inventory/group_vars`
* `./<latest kubespray>/contrib/terraform/openstack/hosts -> ../terraform.py`
* `./<latest kubespray>/contrib/terraform/openstack/group_vars -> ../../../inventory/group_vars`
* `./<latest kubespray>/contrib/network-storage/glusterfs/group_vars -> ../../../inventory/group_vars`
* `./<latest kubespray>/contrib/network-storage/glusterfs/roles/bootstrap-os -> ../../../../roles/bootstrap-os`
* `./kubespray -> <latest kubespray>`


## troubleshooting
in case of ssh connection issues check if there are still ssh folders in /tmp lingering
``` bash
rm /tmp/kubespraytest-k8s-*
```
also cleanse known_hosts from bastion public_ip

## to bring up the deployment
```
ostack/deploy.sh
```
before that, except for sourcing the openstack credentials, the following exports might be needed:
```
# set environment variables used by scripts in cloud-deploy/
export PUBLIC_KEY=""
export PRIVATE_KEY=""
export PORTAL_DEPLOYMENTS_ROOT="$PWD/deployments"
export PORTAL_APP_REPO_FOLDER="$PWD"
export PORTAL_DEPLOYMENT_REFERENCE="deployment-ref-ubuntu"

deployment_dir="$PORTAL_DEPLOYMENTS_ROOT/$PORTAL_DEPLOYMENT_REFERENCE"
if [[ ! -d "$deployment_dir" ]]; then
    mkdir -p "$deployment_dir"
fi
printf 'Using deployment directory "%s"\n' "$deployment_dir"

export TF_VAR_kube_api_pwd=""
export TF_VAR_cluster_name=""
export TF_VAR_number_of_etcd="0"
export TF_VAR_number_of_k8s_masters="1"
export TF_VAR_number_of_k8s_masters_no_floating_ip="0"
export TF_VAR_number_of_k8s_masters_no_etcd="0"
export TF_VAR_number_of_k8s_masters_no_floating_ip_no_etcd="0"
export TF_VAR_number_of_k8s_nodes_no_floating_ip="2"
export TF_VAR_number_of_k8s_nodes="0"
export TF_VAR_public_key_path=""
export TF_VAR_image="Ubuntu16.04"
#export TF_VAR_image="CentOS7-1612"
export TF_VAR_ssh_user="ubuntu"
#export TF_VAR_ssh_user="centos"
#export TF_VAR_flavor_k8s_node="e9ca7478-7957-4237-b3d0-d4767e1de65f" #ext5
export TF_VAR_flavor_k8s_node="11"
#export TF_VAR_flavor_etcd="12"
#export TF_VAR_flavor_k8s_master="91ba172b-cb4c-453c-b7fc-56cb79c78968" #ext5
export TF_VAR_flavor_k8s_master="11"
export TF_VAR_network_name=""
export TF_VAR_floatingip_pool=""

# GlusterFS variables
#export TF_VAR_flavor_gfs_node="e9ca7478-7957-4237-b3d0-d4767e1de65f" #ext5
export TF_VAR_flavor_gfs_node="11"
export TF_VAR_image_gfs="Ubuntu16.04"
export TF_VAR_number_of_gfs_nodes_no_floating_ip="3"
export TF_VAR_gfs_volume_size_in_gb="30"
export TF_VAR_ssh_user_gfs="ubuntu"

export KUBELET_DEPLOYMENT_TYPE="host"
export KUBE_VERSION="v1.8.2"
```

### adding an object store secret to be passed on to helm means adding extra-vars to the in deploy.sh
``` bash
ansible-playbook ... --extra-vars "objectstore_token=asd123lkj890dfg..."
```
this can then be consumed by helm in tasks/main.yaml with_items: jinja2 nomenclature "...,objectstore_token={{objectstore_token}}"
## to destroy the deployment
use
``` bash
terraform destroy --force --input=false --state=deployments/deployment-ref-ubuntu/terraform.tfstate
```

### deployment failure due to unreachable hosts
check ssh known_hosts first (`ssh-keygen -R 193.62.52.158`), then it still might be due to TSI 'live migrations' (moving instances from one openstack host to the other).
kubespraytest-k8s-master-1 : ok=1    changed=0    unreachable=1    failed=0   
kubespraytest-k8s-node-nf-1 : ok=1    changed=0    unreachable=1    failed=0   
kubespraytest-k8s-node-nf-2 : ok=1    changed=0    unreachable=1    failed=0


### redeploy galaxy for development purposes (and there was a previous deployment)
In master node
```
sudo helm delete $(sudo helm list | awk 'NR==2 {print $1;}')
kubectl delete configmaps db-connection
kubectl delete pv glusterfs
kubectl delete secret galaxy-postgres-secret
```
(due to their pre-install hook nature)[https://github.com/kubernetes/helm/issues/960]
./reup_g.sh

### inspect init containers
kubectl get pods
kubectl logs galaxy-k8s-lt2cn -c galaxy-settings-provisioner

### get the env
```
kubectl proxy
ssh -L 30700:localhost:30700 ubuntu@193.62.52.182
```
