import boto3
import json


from utils import auto_scaling_group, launch_template, auto_scaling_policy # import all the helper functions
from config import network, ssh_key, ec2_params, user_data, db, network, elb_param

iam=boto3.client('iam')
asc= boto3.client('autoscaling')
ec2_temp =  boto3.client('ec2')
ec2 =boto3.resource('ec2')
elb = boto3.client('elbv2')


instance_profile_arn = iam.get_instance_profile(
    InstanceProfileName=db['bucket_name'],
)
instance_profile_arn=instance_profile_arn['InstanceProfile']['Arn']

vpc_iterator = ec2.vpcs.filter()
for vpc in vpc_iterator:
    if vpc.tags is None: pass
    elif vpc.tags[0]['Value'] == network['vpc_name']:

        for security_group in vpc.security_groups.filter():
            if security_group.tags is None: pass
            elif security_group.tags[0]['Value'] == network['security_group_name']:
                sg_instance_id = security_group.id

        subnet_ids=[subnet.id for subnet in vpc.subnets.filter()]

# get target group arn
tg = elb.describe_target_groups(
    Names=[elb_param['tg_name']]
)
tg_arn = tg['TargetGroups'][0]['TargetGroupArn']

# create a launch template for autoscaling group
LaunchTemplate = launch_template(
  ec2_temp,
  ec2_params['launch_template_name'],
  instance_profile_arn,
  sg_instance_id,
  subnet_ids[1],
  ec2_params['image_id'],
  ec2_params['instance_type'], 
  ssh_key['key_name'], 
  user_data
  )

template_id = LaunchTemplate['LaunchTemplate']['LaunchTemplateId']
#create auto scaling group
auto_scaling_group(asc, ec2_params['scaling_group_name'], 
                   template_id, network['az1'], network['az2'],subnet_ids[0], subnet_ids[1], tg_arn)

# put scaling policy
auto_scaling_policy(asc,  ec2_params['scaling_group_name'])
