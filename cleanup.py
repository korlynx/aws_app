"""Helper function for resource clean up """
import boto3
from config import iam_param, db, ec2_params, ssh_key, network, elb_param

s3_client = boto3.client('s3')
iam_client= boto3.client('iam')
ec2 = boto3.resource('ec2')
dynamo_client = boto3.client('dynamodb')
elb = boto3.client('elbv2')
asc= boto3.client('autoscaling')
ec2_temp =  boto3.client('ec2')


dynamodbarn=iam_param['DynamoDb_policyArn']
s3arn=iam_param['s3_policyArn']


def delete_daynamodb(dynamo_client, table_name):
    dynamo_client.delete_table(TableName = table_name )
    print(f'--- DynamoDb {table_name} table deleted sucessfully ---')
    
    
def s3_objects(s3_client, bucket_name, key):
    ob = s3_client.get_object(Bucket=bucket_name, Key=key)
    return ob
      
def delete_objects(s3_client, bucket_name, key):
    """Delete list of objects"""
    s3_client.delete_objects(Bucket=bucket_name, Delete={
        'Objects':[
            {
                'Key': key
            },
        ]
    })
    
    print('--- S3 Objects deleted ---')

def delete_s3_objects(s3_client, bucket_name, ):
    response = s3_client.list_objects(
    Bucket=bucket_name,
)

    object_key = response['Contents']
    for key in object_key:
        delete_objects(s3_client, bucket_name, key['Key'])
    
    print('--- S3 bucket objects deleted ---')

def delete_s3_bucket(s3_client, bucket_name):
    """ All objects in the bucket must be deleted before the bucket
    itself can be deleted"""
    s3_client.delete_bucket(Bucket= bucket_name)
    print(f'--- {bucket_name} Bucket deleted ---')

def remove_policy(iam_client, role_name, policyarn):
    iam_client.detach_role_policy(RoleName=role_name, PolicyArn=policyarn)
    print(f'--- {policyarn} policy removed  ---')
    
   
def delete_iam_role(iam_client, role_name):
    remove_policy(iam_client, role_name, dynamodbarn)
    remove_policy(iam_client, role_name, s3arn)
    iam_client.delete_role(RoleName=role_name)
    print(f'--- {role_name} IAM role deleted ---')

def delete_instance_profile(iam_client, profile_name):
    response = iam_client.delete_instance_profile(
    InstanceProfileName=profile_name
    )
def remove_role(iam_client, profile_name, role_name):
    response = iam_client.remove_role_from_instance_profile(
    InstanceProfileName=profile_name,
    RoleName=role_name
    )

def instance_terminate(instance_name):
    instances =ec2.instances.filter()
    print('--- terminating ec2 instance. This may take a moment ---')
    for instance in instances:
        if instance.tags[0]['Value'] == instance_name:
            instance.stop()
            instance.wait_until_stopped()
            # terminate instance
            instance.terminate()
            instance.wait_until_terminated()
            print(f'--- instance {instance_name} successfully terminated ---')
            
        else:
            pass
            print(f'--- instance with name {instance_name} does not exit ---')

def delete_network(ec2, vpc_name, route_table_name):
    vpc_iterator = ec2.vpcs.filter()
    for vpc in vpc_iterator:
        # pass default vpc 
        if vpc.tags is None: pass
        elif vpc.tags[0]['Value'] == vpc_name:
            # delete internet gateway
            for igw in vpc.internet_gateways.filter():
                vpc.detach_internet_gateway(InternetGatewayId=igw.id)
                igw.delete()
    
                # delet vpc security group
            for security_group in vpc.security_groups.filter():
                #
                if security_group.tags is None: pass
                else: security_group.delete()

            # delete vpc subnets
            for subnet in vpc.subnets.filter():
                subnet.delete()

            # # delete vpc
            for route_table in vpc.route_tables.filter():
                if len(route_table.tags) == 0: pass
                elif route_table.tags[0]['Value']==route_table_name:
                    route_table.delete()
    
            vpc.delete()
    print(f'--- {vpc_name} and attached resource deleted ---')
# Delete load balancer listener
def remove_listener(elb, listener_arn):
    response = elb.delete_listener(
    ListenerArn=listener_arn
    )
# Delete load balancer 
def delete_elb(elb, elb_name):
    res = elb.describe_load_balancers(
        Names=[elb_name]
        )
    elb_arn = res['LoadBalancers'][0]['LoadBalancerArn']
    desc_listener = elb.describe_listeners(
    LoadBalancerArn=elb_arn,
    )
    listener_arn=desc_listener['Listeners'][0]['ListenerArn']
    _=remove_listener(elb, listener_arn)
    response = elb.delete_load_balancer(
        LoadBalancerArn=elb_arn
    )
    print(f'--- {elb_name} load balancer deleted ---')

    
def deregister_target_group(elb, tg_name, instance_id):
    tg_ = elb.describe_target_groups(Names=[tg_name])
    tg_arn = tg_['TargetGroups'][0]['TargetGroupArn']
    tg_ = elb.describe_target_groups(
        Names=[tg_name]
    )
    elb.deregister_targets(
        TargetGroupArn=tg_arn,
        Targets=[{
                'Id': instance_id,
                'Port': 80,
            }
        ]
    )
    print('--- target group disregistered ---')

def delete_target_group(elb, tg_name):
    tg_ = elb.describe_target_groups(Names=[tg_name])
    tg_arn = tg_['TargetGroups'][0]['TargetGroupArn']
    elb.delete_target_group(TargetGroupArn=tg_arn)
    print('--- load balancer target group deleted ---')

def describe_policy_name(asc, auto_scaling_group_name):
    response = asc.describe_policies(AutoScalingGroupName=auto_scaling_group_name)
    pn = response#['ScalingPolicies']#[0]['PolicyName']
    return pn

def remove_auto_scaling_policy(asc, auto_scaling_group_name, policy_name):
    response = asc.delete_policy(
    AutoScalingGroupName=auto_scaling_group_name,
    PolicyName=policy_name
    )

def delete_autoscaling_group(asc, group_name, policy_name):
    #des_asc = asc.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name,] )
    #autoscaling_policy_arn = des_asc['AutoScalingGroups'][0]['AutoScalingGroupARN']
    remove_auto_scaling_policy(asc, group_name, policy_name)
    response = asc.delete_auto_scaling_group(
    AutoScalingGroupName=group_name,
    ForceDelete=True
    )
    print('--- autoscaling group deleted ---')
    
def delete_launch_template(ec2_temp, template_name):
    response = ec2_temp.delete_launch_template(
    LaunchTemplateName=template_name
    )
    print('--- Launch Template deleted ---')


ec2_id = ec2.instances.filter()
instance_ids= [x.id for x in ec2_id]
instance_id =instance_ids[0]

#policy_name = describe_policy_name(asc, ec2_params['scaling_group_name'])
#remove_auto_scaling_policy(asc, ec2_params['scaling_group_name'], ec2_params['policy_name'])

#delete autoscaling group
delete_autoscaling_group(asc, ec2_params['scaling_group_name'], ec2_params['policy_name'])

#delete launch template
delete_launch_template(ec2_temp, ec2_params['launch_template_name'])

#delete target group
deregister_target_group(elb,  elb_param['tg_name'], instance_id)

# # #delete load balancer
delete_elb(elb, network['elb_name'])
waiter = elb.get_waiter('load_balancers_deleted')
waiter.wait(Names=[network['elb_name']])

delete_target_group(elb, elb_param['tg_name'])
# # delete ec2 instance
instance_terminate(ec2_params['instance_name'])

## delete ssh key
key_pair = ec2.KeyPair(ssh_key['key_name'])
key_pair.delete()

# # delete database and storage bucket
delete_s3_bucket(s3_client, db['bucket_name'])
delete_daynamodb(dynamo_client, db['dynamo_table_name'])

#delete IAM role
profile_name=db['bucket_name']
remove_role(iam_client, profile_name, iam_param['role_name'])
delete_instance_profile(iam_client, profile_name)
delete_iam_role(iam_client, iam_param['role_name'])

# delete vpc, route table, security group
delete_network(ec2, network['vpc_name'], network['route_table_name'])


