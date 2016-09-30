#!/usr/bin/env python
import boto3
from collections import defaultdict

filters = [{'Name':'tag:InstanceName','Values':['web*']}]

def get_conn():
    return boto3.resource('ec2')

def get_instance_info(ec2): 
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
    return ec2info

    
ec2data = get_instance_info(get_conn())
for instance_id, instance in ec2data.items():
    print instance
    #for key in attributes:
    #    print "{0} : {1}".format(key,instance[key])

