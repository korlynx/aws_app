# Helper functions for creating AWS resources 


def create_aws_vpc(ec2_resource, vpc_cidr_block, tag_value):
    """ ec2_resource: ec2.boto3('ec2')
        vpc_cidr_block: vpc cidr block range
        tag_value: tag name for the VPC
    """
    vpc = ec2_resource.create_vpc(
        CidrBlock=vpc_cidr_block,
        TagSpecifications=[
            {'ResourceType': 'vpc',
             'Tags': [{'Key': 'Name', 'Value': tag_value}]
            }
        ]
    )
    vpc.wait_until_available()
    return vpc
# create internet gateway
def vpc_igw(ec2_resource, tag_value):
    '''tag_value: should be what you want to name the internet gateway
        ec2_resource: ec2 resource 'boto3.resource('ec2')'
    '''
    igw = ec2_resource.create_internet_gateway(
        TagSpecifications=[
            {'ResourceType': 'internet-gateway',
             'Tags': [{'Key': 'Name','Value': tag_value}]
            }
        ],
    )
    return igw

# attach internet gateeway
def attach_gateway_to_vpc(igw, vpcid):
    """
        igw= response from created internet gateway
        vpcid = vpc id
    """
    response = igw.attach_to_vpc(VpcId=vpcid)
    if response:
        print(f'--- Internet gateway succesfully attached to {vpcid} ---')

# create rooute table
def vpc_route_table(vpc, igw_id, tag_value):
    """
        vpc: vpc response
        igw_id: internet gateway id
        tag_value: routebale name
    """
    route_table = vpc.create_route_table(
        TagSpecifications=[
            {'ResourceType': 'route-table',
            'Tags': [{'Key': 'Name','Value': tag_value}]
            }
        ],
    )
    #create route
    route = route_table.create_route(GatewayId=igw_id, 
                             DestinationCidrBlock='0.0.0.0/0')
    print(f'--- route table with name: {tag_value} created ---')
    return route_table
    
# create subnet
def vpc_subnet(vpc, az, subnet_cidir, tag_value):
    """
    Args:
        vpc : vpc resource response
        az (string): availabilty zone
        subnet_cidir (string): subnet cidir block range
        tag_value (string): subnet name

    Returns:
        string: subnet id
    """
    subnet = vpc.create_subnet(
        TagSpecifications=[
            {
                'ResourceType': 'subnet',
                'Tags': [{'Key': 'Name','Value': tag_value}]
            }
        ],
        AvailabilityZone=az,
        CidrBlock=subnet_cidir
    )
    return subnet.id

# associate route table
def associate_route_table(vpc_route_table, *subnet_ids):
    """associate a list of subnet ids

    Args:
        vpc_route_table : route table response
    """
    
    for subnetId in subnet_ids:
        vpc_route_table.associate_with_subnet(SubnetId=subnetId)
    print(f'--- route table associated to subnets ---')

# create security group        
def security_group(ec2_resource, tag_value, vpcid):
    """_summary_

    Args:
        ec2_resource : ec2 resource response
        tag_value (string): eSecurity group name
        vpcid (string): vpc id

    Returns:
        _type_: _description_
    """
    # Create security group 
    sg=ec2_resource.create_security_group(
        Description="App security group for HTTP access",
        GroupName=tag_value,
        VpcId=vpcid,
        TagSpecifications=[{
                'ResourceType': 'security-group',
                'Tags': [{'Key': 'Name','Value': tag_value}]
            }]   
    )
    return sg

# set listeners for security group
def sg_ingress(sg, ssh=True):
    '''Authorize ingress security group
    sg (object)
    '''
    
    if ssh:
        sg.authorize_ingress(
            IpPermissions=[
                {
                    'FromPort': 80,
                    'IpProtocol': 'tcp',
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },
                {
                    'FromPort': 22,
                    'IpProtocol': 'tcp',
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },
                {
                    'FromPort': 443,
                    'IpProtocol': 'tcp',
                    'ToPort': 443,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            ])
    else:
        sg.authorize_ingress(
            IpPermissions=[{
                    'FromPort': 80,
                    'IpProtocol': 'tcp',
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        ])

    

# create SSH key pair
def key_pair(ec2_resource, key_name, tag_value):
    ''' Create key for SSH key'''
    key_pair = ec2_resource.create_key_pair(
        KeyName=key_name,
        KeyType='rsa',
        TagSpecifications=[
            {
                'ResourceType':'key-pair',
                'Tags':[{'Key':'Name','Value': tag_value}]
            }
        ],
        KeyFormat='pem'
    )
    print(f'--- key-pair for EC2 instance created ---')

# Create EC2 instance    
def ec2_instance(ec2_resource, image_id, instance_type, key_name,
                 az, user_data, sg_id, subnet_id, instance_profile_arn, tag_value):
    """Create and Launch and an EC2 instance inside the created VPC

    Args:
        ec2_resource (obect): ec2 client or resource object
        image_id (string): AWS AMI id
        instance_type (string): AWS instance type
        key_name (string): ssh key-pair name
        az (string): Availability region
        user_data (string): strings of shell commands to be excuted during instance start-up
        sg_id (string): security group id
        subnet_id (string): subnet id
        instance_profile_arn (string): role instance profile ARN
        tag_value (string): EC2 instance name

    Returns:
        string: returns the id of the created ec2 instance
    """
    instances = ec2_resource.create_instances(
        ImageId=image_id,
        InstanceType=instance_type,
        KeyName=key_name,
        Placement={'AvailabilityZone': az},
        MaxCount=1,
        MinCount=1,
        UserData=user_data, # add your custom user-data script here
        BlockDeviceMappings=[{
                'DeviceName':'/dev/sda1',
                'Ebs': {
                    'DeleteOnTermination': True,
                    'VolumeSize': 8,
                    'VolumeType':'gp3',

                }
            }],
        NetworkInterfaces=[
            {
                'AssociatePublicIpAddress': True,
                'Groups': [sg_id],
                'SubnetId': subnet_id,
                'DeviceIndex': 0
            }
        ],
        IamInstanceProfile={'Arn':instance_profile_arn},
        TagSpecifications=[
            {
                'ResourceType':'instance',
                'Tags': [{'Key':'Name','Value':tag_value}]
            }
        ],
    )
    print('--- Launching ec2 instance. Instance my take a while to be available ---')
    instances[0].wait_until_running()
    print(f'--- instance with {instances[0].id} created ---')
    return instances[0].id

# create a load balancer
def elastic_load_balancer(elb_client, elb_name, subnet1_id, 
                          subnet2_id, elb_sg_id, tag_value):
    """Create Elastic Application load balancer

    Args:
        elb_client (object)
        elb_name (string): Load balancer name
        subnet1_id (string): Public subnet 1
        subnet2_id (string): public subnet 2
        elb_sg_id (string): Load balancer security group ID
        tag_value (string): Laod balanacer name

    Returns:
        dict
    """
    lb=elb_client.create_load_balancer(
        Name=elb_name,
        Subnets=[subnet1_id, subnet2_id],
        SecurityGroups=[elb_sg_id],
        Tags=[{'Key':'Name','Value':tag_value}],
        Type='application',
        IpAddressType='ipv4',
    )
    print(f'--- {elb_name} load balancer created, wait for load balancer to be available ---')
    elb_waiter = elb_client.get_waiter('load_balancer_available')
    elb_waiter.wait(Names=[elb_name])
    print(f'--- {elb_name} load balancer is now available ---')
    return lb

# create a load balancer target group
def target_group(elb_client, tg_name, vpcid, tag_value):
    """Create target group for load balancer

    Args:
        elb_client (object)
        tg_name (string): Target group name
        vpcid (string): vpc id
        tag_value (string): Target group name

    Returns:
        dict
    """
    tg=elb_client.create_target_group(
        Name=tg_name,
        Protocol='HTTP',
        ProtocolVersion='HTTP1',
        Port=80,
        VpcId=vpcid,
        HealthCheckProtocol='HTTP',
        HealthCheckEnabled=True,
        HealthCheckIntervalSeconds=50,
        HealthCheckTimeoutSeconds=40,
        HealthyThresholdCount=2,
        UnhealthyThresholdCount=5,
        TargetType='instance',
        Tags=[{'Key': 'Name','Value': tag_value}],
        IpAddressType='ipv4'
    )
    print('--- target group created ---')
    return tg

# register target groups
def register_targetgroup(elb_client, tg_arn, inst_id):
    """register target group

    Args:
        elb_client (object)
        tg_arn (str): Target group ARN
        inst_id (str): EC" instance ID
    """
    # register targets
    elb_client.register_targets(
        TargetGroupArn=tg_arn,
        Targets=[{
                'Id':inst_id,
                'Port':80,
            }]
    )
    print(f'--- {inst_id} Target group registered ---')

def load_balancer_listener(elb_client, elb_arn, tg_arn):
    """Add listener to created load balancer

    Args:
        elb_client (object)
        elb_arn (str): Load balancer ARN
        tg_arn (str): Target group ARN

    Returns:
        dict
    """
    response = elb_client.create_listener(
    LoadBalancerArn=elb_arn,
    Protocol='HTTP',
    Port=80,
    DefaultActions=[{
        'Type': 'forward',
        'TargetGroupArn': tg_arn, 
        },
    ])
    print('--- Load balancer listerner created ---')
    return response

# Create a launch template
def launch_template(ec2_client, template_name, instance_profile_arn,
                    sg_id, subnet_id, image_id, instance_type, key_name, user_data):
    """Create launch tamplate for autoscaling

    Args:
        ec2_client (object)
        template_name (string): launch teplate name
        instance_profile_arn (string): Service role prifile ARN
        sg_id (str): instance security goup
        subnet_id (str): subnet id
        image_id (str): AMI id
        instance_type (str): instance type
        key_name (str): SHH key
        user_data (str): User data

    Returns:
        dict
    """
    template = ec2_client.create_launch_template(
        LaunchTemplateName=template_name,
        VersionDescription='My sample launch template',
        LaunchTemplateData={
            'IamInstanceProfile': {'Arn':instance_profile_arn},
            'BlockDeviceMappings': [{
                'DeviceName':'/dev/sda1',
                'Ebs':{
                    'DeleteOnTermination': True,
                    'VolumeSize':8,
                    'VolumeType':'gp3'                     
                }
               
            }],
            'NetworkInterfaces': [{
                'AssociatePublicIpAddress': True,
                'DeviceIndex': 0,
                'Groups': [sg_id],
                'SubnetId': subnet_id
            }],
            'ImageId': image_id,
            'InstanceType':instance_type,
            'KeyName': key_name,
            'UserData': user_data,
            'TagSpecifications': [{
                    'ResourceType': 'instance',
                    'Tags': [{
                            'Key': 'Name',
                            'Value': 'webservers',
                        }],
                }],
        }
        
    )
    print('--- Launch template created ---')
    return template


# create auto scaling group
def auto_scaling_group(autoScaling_client, autoscaling_group_name, template_id,
                        az1, az2, subnet1_id, subnet2_id, tg_arn):
    """Create autoscaling group

    Args:
        autoScaling_client (object): _description_
        autoscaling_group_name (string): _description_
        template_id (string): Launch template id
        az1 (string): Availability zone
        az2 (string): Availability zone
        subnet1_id (string): Public subnet id
        subnet2_id (string): Public subnet id
        tg_arn (string): Target group ARN

    Returns:
        dict
    """
    as_group = autoScaling_client.create_auto_scaling_group(
        AutoScalingGroupName=autoscaling_group_name,
        LaunchTemplate={
            'LaunchTemplateId': template_id,
            'Version': '$Default'},
        MinSize=2,
        MaxSize=4,
        DesiredCapacity=2,
        AvailabilityZones=[az1, az2],
        VPCZoneIdentifier= f"{subnet1_id}, {subnet2_id}",
        TargetGroupARNs=[tg_arn],
        HealthCheckType='ELB',
        HealthCheckGracePeriod=300,
    )
    print('--- auto scaling group created ---')
    return as_group

# Put policy
def auto_scaling_policy(autoScaling_client, autoscaling_group_name):
    """attach policy to the auto scaling group

    Args:
        autoScaling_client (object)
        autoscaling_group_name (string)
 ion_    """
    as_p = autoScaling_client.put_scaling_policy(
    AutoScalingGroupName=autoscaling_group_name,
    PolicyName='alb1000-target-tracking-scaling-policy',
    PolicyType='TargetTrackingScaling',
    TargetTrackingConfiguration={
        'PredefinedMetricSpecification': {
            'PredefinedMetricType': 'ASGAverageCPUUtilization',
            # 'ResourceLabel': resource_label,
        },
        'TargetValue': 60.0}
    )
    print('--- scaling policy attached to auto scaling group ---')


# create resource role
def resource_role(iam, role_name, role_policy):
    """Create AWS IAM role

    Args:
        iam (object): iam boto3 client
        role_name (str): assume role name
        role_policy (Json): EC2 service policy
    """
    resource_role =iam.create_role(
        RoleName=role_name,
        MaxSessionDuration=18000,
        AssumeRolePolicyDocument=role_policy
    )
    print(f'--- {role_name} Role created ---')

# attach policy
def attach_policy(iam,role_name, policy_arn):
    """Attach a manged policy to a IAM role

    Args:
        iam (object): iam boto3 client
        role_name (str): assume role name
        policy_arn (str): managed policy ARN
    """
    _ = iam.attach_role_policy(
        RoleName=role_name,
        PolicyArn=policy_arn
    )
    print(f'--- {policy_arn} Role policy attached ---')

# create bucket
def bucket(s3, bucket_name, region):
    """create s3 bucket in a specified region

    Args:
        s3 (object): s3 resource object
        bucket_name (str): s3 bucket name
        region (str): AWS region

    Returns:
        dict
    """
    bucket = s3.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={
            'LocationConstraint':region
        }
    )
    return bucket

# set bucket policy
def set_bucket_policy(s3, bucket_name, bucket_policy):
    """Put bucket policy to the created s3 bucket

    Args:
        s3 (object): _description_
        bucket_name (str): s3 bucket name
        bucket_policy (json): bucket policy
    """
    s3_bucket_policy = s3.put_bucket_policy(
        Bucket = bucket_name,
        Policy=bucket_policy
    )
    print('--- Bucket policy attached ---')


# create dynamodb database
def dnamo_database(dynamodb, table_name):
    """create a dynamodb table

    Args:
        dynamodb (object)
        table_name (string): DynamoDB table name
    """
    dynamo_table = dynamodb.create_table(
        TableName=table_name,
        AttributeDefinitions=[{'AttributeName':'id','AttributeType':'S'}],
        KeySchema=[{
                'AttributeName':'id',
                'KeyType':'HASH'
            }],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    print('--- DynamoDb Created ---')

    