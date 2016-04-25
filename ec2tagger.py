#!/usr/bin/env python


import boto.ec2.elb
import boto.ec2
import boto3
import argparse

#get command args
parser = argparse.ArgumentParser()
parser.add_argument("region", help="specifies the EC2 region; e.g. 'us-west-1'")
parser.add_argument("keytag", help="specifies the key tag; e.g. 'CostAlloc'")
parser.add_argument("--tagvols", help='tag volumes', action="store_true")
parser.add_argument("--taglbs", help='tag load balancers', action="store_true")

args = parser.parse_args()
key_tag = (args.keytag)
region = (args.region)
vol_func = (args.tagvols)
lb_func = (args.taglbs)





def tag_volumes():
    """Get Key/Value tags from Instances 
    and apply them to the Instance's Volumes"""
    print 'Gathering tag information for Volumes...'

#connect to EC2 and get instances and volumes
    ec2_conn = boto.ec2.connect_to_region(region)
    reservations = ec2_conn.get_all_instances()
    instances = [i for r in reservations for i in r.instances]
    vol = ec2_conn.get_all_volumes()

    inst_vol_dict = {}

    for volumes in vol:

        filter = {'block-device-mapping.volume-id':volumes.id}
        volumesinstance = ec2_conn.get_all_instances(filters=filter)

        ids = [z for k in volumesinstance for z in k.instances]
         
        #set values for instances and their volumes  
        for s in ids:
        	instance_id = s.id 
        	volume_id = volumes.id

        	
            
        #Create a dict with instanceid/keytag as key/value
        for res in reservations:
            for inst in res.instances:
                
                if key_tag in inst.tags:
                    inst_vol_dict [ inst.id ] = inst.tags[key_tag]

        #use boto function 'create_tags'       
        try:
            instance_tag = inst_vol_dict[instance_id]
            print 'Tagging volumes... %s' % volume_id
            ec2_conn.create_tags([volume_id], {key_tag: instance_tag})
        except:
            pass 




def tag_load_balancers():
    """Get Key/Value tags from Instances 
    and apply them to the Instance's Load Balancers"""

    print 'Gathering information for Load Balancers...'
    #connect to EC2 and get load balancers
    client = boto3.client('elb', region_name = region)
    elb = boto.ec2.elb.connect_to_region(region)
    lb_conn = elb.get_all_load_balancers()

    instance_elb_dict = {}
    instance_tag_dict = {}

    #create a dict with instanceid/loadbalancer as key/value
    for b in lb_conn:
        lb = elb.get_all_load_balancers([b.name])[0]
        
        for instance_info in lb.instances:
            instance_elb_dict [ instance_info.id ] = b.name 
            

    #connect to EC2 and get instances
    inst_conn = boto.ec2.connect_to_region(region)
    reservations = inst_conn.get_all_instances()

    #create a dict with instanceid/tag as key/value
    for res in reservations:
        for inst in res.instances:
            
            if key_tag in inst.tags:
                instance_tag_dict [ inst.id ] = inst.tags[key_tag]


    #get the instance id from load balancer metadata
    for b in lb_conn:
        lb = elb.get_all_load_balancers([b.name])[0]
        
        for instance_info in lb.instances:
            inst_id = instance_info.id

        #pull matching tags and load balancer info from dicts
        try:
            inst_tag = instance_tag_dict[inst_id]
            inst_elb = instance_elb_dict[inst_id]
            print 'Tagging Load Balancer... %s' % inst_elb 

       


            response = client.add_tags(
        
                LoadBalancerNames=[
                    inst_elb,
                    ],
                Tags=[
                    {
                    'Key': key_tag,
                    'Value': inst_tag
                    },
                ]
            )
        except:
            pass    


if __name__ == "__main__": 

    if vol_func:
        tag_volumes()
    if lb_func:
        tag_load_balancers()
