#!/bin/bash

printf "Files required: \nupgrade-from-v1.0-apply.yaml\nupgrade-from-v1.0-create.yaml\n"

ceph_status=`kubectl -n rook-ceph exec -it $(kubectl -n rook-ceph get pod -l "app=rook-ceph-tools" -o jsonpath='{.items[0].metadata.name}') -- ceph status|grep health`

printf "Checking rook health...\n"
if [[ $ceph_status =~ "HEALTH_WARN" ]]; then 
  printf "Cluster is not healthy...\nStabilize the existing instance prior to upgrading\n"
  printf "Run the following command for more information\n'kubectl -n rook-ceph exec -it $(kubectl -n rook-ceph get pod -l "app=rook-ceph-tools" -o jsonpath='{.items[0].metadata.name}') -- ceph status'\n"
  printf "aborting upgrade\n"
  exit 1
fi

create_upgrade=`kubectl create -f upgrade-from-v1.0-create.yaml`
echo $create_upgrade

apply_upgrade=`kubectl apply -f upgrade-from-v1.0-apply.yaml`
echo $apply_upgrade

execute_upgrade=`kubectl -n rook-ceph set image deploy/rook-ceph-operator rook-ceph-operator=rook/ceph:v1.1.9`
