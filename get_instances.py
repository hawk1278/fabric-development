#!/usr/bin/env python
import boto3
from collections import defaultdict
ec2 = boto3.resource('ec2')
filters = [{'Name':'tag:InstanceName','Values':['web*']}]
instances = ec2.instances.filter(
    Filters=filters
)
ec2info = defaultdict()
attributes = ['name','public_ip']
for instance in instances:
    for tag in instance.tags:
        if 'InstanceName' in tag['Key']:
            name = tag['Value']
    ec2info[instance.id] = {
        'name' : name,
        'public_ip' : instance.public_ip_address,
        #'public_dbs' : instance.public_dns_name
    }

for instance_id, instance in ec2info.items():
    print instance
    #for key in attributes:
    #    print "{0} : {1}".format(key,instance[key])

