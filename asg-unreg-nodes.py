#!/usr/bin/env python

"""
asg-unreg-nodes.py
List autos-scaled nodes that failed to register with Yarn Resource Manager
Sample config
{
    "access_key": "key",
    "secret_key": "secret",
    "group_name": "datapipeline-in-stag-spot-asg"

    # optional: depending on running on the master/any node
    "HOSTNAME": "datapipeline-in-master.stag.indix.tv"
}
"""
import boto
import boto.ec2.autoscale
from boto.ec2.autoscale import AutoScaleConnection
import requests
import json
import socket

config = json.load(open("config.json"))
access_key = config['access_key']
secret_key = config['secret_key']
group_name = config['group_name']

def get_asg_instances():
    ec2_conn = boto.connect_ec2(access_key, secret_key)
    asg_conn = AutoScaleConnection(access_key, secret_key)

    group = asg_conn.get_all_groups([group_name])[0]
    instance_ids = [i.instance_id for i in group.instances]
    reservations = ec2_conn.get_all_instances(instance_ids)
    instances = [i for r in reservations for i in r.instances]
    private_ips = [i.private_ip_address for i in instances]
    return private_ips

def get_yarn_slaves():
    node_list=[]
    if socket.getfqdn().find('.') >= 0:
        HOSTNAME = socket.getfqdn()
    else:
        HOSTNAME = socket.gethostbyaddr(socket.gethostname())[0]
    JOB_TRACKER_URL = "http://" + HOSTNAME + ":8088/ws/v1/cluster/nodes"

    response = requests.get(JOB_TRACKER_URL)
    if (response.status_code == 200):
        yarn_cluster = response.json()

    for val in range(len(yarn_cluster['nodes']['node'])):
        if yarn_cluster['nodes']['node'][val]['state'] == "RUNNING":
             node_list.append( yarn_cluster['nodes']['node'][val]['nodeHostName'])
    return node_list

def main():
    unreg_nodes = [c for c in get_asg_instances() if c not in get_yarn_slaves()]
    print("List of asg nodes not registered with yarn cluster:")
    print ('[%s]' % ', '.join(map(str, unreg_nodes)))

if __name__ == '__main__':
    main()
