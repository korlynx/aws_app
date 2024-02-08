import boto3
import json
from utils import set_bucket_policy
from config import db, iam_param, ec2_params

s3=boto3.client('s3')
iam=boto3.client('iam')


roleArn = iam.get_role(RoleName=iam_param['role_name'])
role_arn = roleArn['Role']['Arn']
# create an instance profile for role
instance_profile_response = iam.create_instance_profile(
    InstanceProfileName=db['bucket_name'],
    Path='/',
    Tags=[
        {
            'Key': 'Name',
            'Value': ec2_params['instance_name']
        },
    ]
)

# define bucket policy
bucket_policy = json.dumps({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "s3bucketpolicyforinstancerole",
      "Action": "s3:*",
      "Effect": "Allow",
      "Resource": f"arn:aws:s3:::{db['bucket_name']}/*",
      "Principal": {
        "AWS": [
          f"{role_arn}"
        ]
      }
    }
  ]
})
# add role to instance profile
role_instance_profile = iam.add_role_to_instance_profile(
    InstanceProfileName=db['bucket_name'],
    RoleName=iam_param['role_name']
)
# Set bucket policy
set_bucket_policy(s3, db['bucket_name'], bucket_policy)
