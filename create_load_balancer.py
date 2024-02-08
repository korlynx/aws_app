import boto3
from utils import target_group, register_targetgroup, elastic_load_balancer, load_balancer_listener
from config import network, ec2_params,elb_param

ec2=boto3.resource('ec2')
elb = boto3.client('elbv2')

# get vpc, subnets and load balancer security group id
vpc_iterator = ec2.vpcs.filter()
for vpc in vpc_iterator:
  
    if vpc.tags is None: pass
    elif vpc.tags[0]['Value'] == network['vpc_name']:
        vpc_id = vpc.id
        print(vpc_id)
           
        for security_group in vpc.security_groups.filter():
            if security_group.tags is None: pass
            elif security_group.tags[0]['Value'] == network['elb_security_group_name']:
                elb_sg_id = security_group.id
                print(elb_sg_id)

        subnet_ids=[subnet.id for subnet in vpc.subnets.filter()]
        print(subnet_ids)

#get instance id
instances =ec2.instances.filter()
for instance in instances:
    if instance.tags[0]['Value'] == ec2_params['instance_name']:
        instance_id= instance.id
print(instance_id)

# create Target group
tg = target_group(elb, elb_param['tg_name'], vpc_id, elb_param['tag_value'])
tg_arn = tg['TargetGroups'][0]['TargetGroupArn']
print(tg_arn)
#register target group
register_targetgroup(elb, tg_arn, instance_id)

# #create an application load balancer, to balance and route traffic to other subnet
elb_response = elastic_load_balancer(elb, network['elb_name'], subnet_ids[0],
                                     subnet_ids[1], elb_sg_id, network['elb_tag'])

elb_arn = elb_response['LoadBalancers'][0]['LoadBalancerArn']
elb_dns = elb_response['LoadBalancers'][0]['DNSName']
print(elb_dns)

# Put load balancer listener   
lst = load_balancer_listener(elb, elb_arn, tg_arn)
