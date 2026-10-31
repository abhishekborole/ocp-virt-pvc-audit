"""Audit live PVC status and optionally expand one claim after checking storage-class expansion support."""
import argparse
from decimal import Decimal
import json
import sys
import subprocess
from datetime import datetime, timezone
from oc_client import Client, VM, VMI, MIG, SNAP, quantity, age_hours, condition, require_name, stopped, escape, migration


def execute(client,args):
    if args.expand_size:
        pvc = client.get('persistentvolumeclaims', require_name(args))
        old = pvc['spec']['resources']['requests']['storage']
        if quantity(args.expand_size) <= quantity(old): raise ValueError('New size must be larger than the current storage request')
        storage_class = client.get('storageclasses.storage.k8s.io', pvc['spec']['storageClassName'])
        if not storage_class.get('allowVolumeExpansion'): raise ValueError('Storage class does not allow expansion')
        return client.patch('persistentvolumeclaims', pvc, [{'op':'replace','path':'/spec/resources/requests/storage','value':args.expand_size}], args.apply)
    return [{'name':pvc['metadata']['name'], 'phase':pvc.get('status',{}).get('phase'), 'requested':pvc['spec']['resources']['requests']['storage'],
             'capacity':pvc.get('status',{}).get('capacity',{}).get('storage'), 'storage_class':pvc['spec'].get('storageClassName'), 'conditions':pvc.get('status',{}).get('conditions',[])} for pvc in client.items('persistentvolumeclaims')]


def main():
    parser = argparse.ArgumentParser(description='Audit live PVC status and optionally expand one claim after checking storage-class expansion support.')
    parser.add_argument('--context',required=True,help='Explicit existing oc kubeconfig context')
    parser.add_argument('--namespace',required=True,help='Namespace for workload operations')
    parser.add_argument('--name',help='Exact workload/resource name where required')
    parser.add_argument('--apply',action='store_true',help='Execute the requested change; default is preview')
    parser.add_argument('--expand-size', help='New Kubernetes storage quantity, for example 200Gi')
    args = parser.parse_args()
    try:
        result = execute(Client(args.context,args.namespace),args)
        print(json.dumps({'context':args.context,'namespace':args.namespace,'collected_at':datetime.now(timezone.utc).isoformat(),'result':result},indent=2))
    except (RuntimeError,ValueError,KeyError,OSError,TimeoutError,subprocess.SubprocessError) as error:
        print(str(error),file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__': raise SystemExit(main())
