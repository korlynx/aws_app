import boto3
from utils import * # import all the helper functions
from config import network, ssh_key, ec2_params, user_data, db


# Before using Boto3, you need to set up authentication credentials for your AWS account 
# using either the IAM Console or the AWS CLI. In this tutorial, i have configured my authentication using the 
# AWS CLI 'aws configure' before hand.
#
# You can also use boto3 resource to setup your authentication credentials
# ec2 = boto3.resource('ec2', aws_access_key_id='AWS_ACCESS_KEY_ID',
#                     aws_secret_access_key='AWS_SECRET_ACCESS_KEY',
#                     region_name='eu-central-1')

iam=boto3.client('iam')
ec2=boto3.resource('ec2')


# # create vpc
vpc_response = create_aws_vpc(ec2, network['vpc_cidr_block'], network['vpc_name'])
vpc_id = vpc_response.id

# create internet gateway and attach it to the vpc
igw=vpc_igw(ec2, network['igw_name'])
attach_gateway_to_vpc(igw, vpc_id)
igw_id = igw.id


# create route table
vpc_route_table = vpc_route_table(vpc_response, igw_id, network['route_table_name'])

# create subnets  in two different availability zones for high reliabiility
subnet1_id = vpc_subnet(vpc_response, network['az1'], network['subnet1_cidr_block'], network['subnet_names'][0])
subnet2_id = vpc_subnet(vpc_response, network['az2'], network['subnet2_cidr_block'], network['subnet_names'][1])
subnet_ids = (subnet1_id, subnet2_id)
# associate route table to both subnets
associate_route_table(vpc_route_table, *subnet_ids)

# create security groups for instance and elastic load balancer
sg_instance = security_group(ec2, network['security_group_name'], vpc_id)
sg_ingress(sg_instance, ssh=True)
sg_instance_id = sg_instance.id
# security group for elastic load balancer
sg_elb = security_group(ec2, network['elb_security_group_name'], vpc_id)
sg_ingress(sg_elb, ssh=False)
sg_elb_id = sg_elb.id

# create key-pair for ssh-ing into ec2 instance
key_pair(ec2, ssh_key['key_name'], ssh_key['key_value'])

# get instance profile
instance_profile_arn = iam.get_instance_profile(
    InstanceProfileName=db['bucket_name'],
)
instance_profile_arn=instance_profile_arn['InstanceProfile']['Arn']


# launch ec2 instance in one of the subnets, the function returns the instance id
instance_id = ec2_instance(
  ec2, ec2_params['image_id'], 
  ec2_params['instance_type'], 
  ssh_key['key_name'], 
  network['az1'],   
  user_data,
  sg_instance_id,
  subnet1_id,
  instance_profile_arn,
  ec2_params['instance_name']
)




