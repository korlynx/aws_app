# Configuration file
import json
import base64


# Netwok parameters
network = {
    'region':'eu-central-1',
    'vpc_cidr_block':'172.20.0.0/16',
    'vpc_name':'app-vpc',
    'igw_name':'app-igw',
    'route_table_name' :'app-routeTable',
    'az1' : 'eu-central-1a',
    'az2' : 'eu-central-1c',
    'subnet1_cidr_block' : '172.20.1.0/24',
    'subnet2_cidr_block' : '172.20.2.0/24',
    'subnet_names' : ['app-subnet1', 'app-subnet2'],
    'security_group_name':'app-securitygroup',
    'elb_security_group_name' :'elb-sg',
    'elb_name':'app-elb',
    'elb_tag':'my-tg'
    
}

# ssh key pair
ssh_key = {
    'key_name':'app-key',
    'key_value':'my-key'
}


# ec2 instance parameters
ec2_params={
    'image_id':'ami-0faab6bdbac9486fb',
    'instance_type':'t2.micro',
    'instance_name':'employee-app',
    'launch_template_name':'app-template',
    'scaling_group_name':'app-autoscalinggroup',
    'policy_name':'alb1000-target-tracking-scaling-policy'
}


# IAM
iam_param={
    'role_name':'employeeapp-dynamos3',
    'role_policy':json.dumps({
        'Version' : '2012-10-17',
        'Statement': [ {
            'Effect': 'Allow',
            'Principal': {
                "Service": ['ec2.amazonaws.com']
            },
            'Action': ['sts:AssumeRole']
        } ]
    }),
    's3_policyArn':'arn:aws:iam::aws:policy/AmazonS3FullAccess',
    'DynamoDb_policyArn':'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess'
}


# database and storage parameters
db={
    'bucket_name' : 'mytestbucket-7070',
    'dynamo_table_name':'Employees', # Based of the App configuration

}

elb_param={
    'tg_name':'app-targetgroup',
    'tag_value':'my-tg'
}

# user data automates the  app set up scrip on launch of the EC2 instance
user_data=base64.b64encode(b"""#!/bin/bash -ex
apt-get update && DEBIAN_FRONTEND=noninteractive apt-get -y install python3-pip
apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install unzip
git clone https://github.com/korlynx/aws_app.git
cd aws_app/
unzip FlaskApp.zip
cd FlaskApp/
pip install -r requirements.txt
DEBIAN_FRONTEND=noninteractive apt-get -y install stress
export PHOTOS_BUCKET={db['bucket_name']}
export AWS_DEFAULT_REGION=eu-central-1
export DYNAMO_MODE=on
FLASK_APP=application.py /usr/local/bin/flask run --host=0.0.0.0 --port=80
""").decode("ascii")