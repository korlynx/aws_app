import boto3
from utils import resource_role, bucket, dnamo_database, attach_policy
from config import network, iam_param, db


# Before using Boto3, you need to set up authentication credentials for your AWS account 
# using either the IAM Console or the AWS CLI. In this tutorial, i have configured my authentication using the 
# AWS CLI 'aws configure' before hand.

iam=boto3.client('iam')
s3=boto3.client('s3')
DynamoDb=boto3.client('dynamodb')

# create a role and attach a resource based policy
resource_role =resource_role(iam, iam_param['role_name'], iam_param['role_policy'])
#attach service policies to the created role
attach_policy(iam, iam_param['role_name'], iam_param['s3_policyArn'])
attach_policy(iam, iam_param['role_name'], iam_param['DynamoDb_policyArn'])

# create s3 bucket 
s3_bucket = bucket(s3, db['bucket_name'], network['region'])
s3_bucket_exists_waiter = s3.get_waiter('bucket_exists')
s3_bucket_exists_waiter.wait(Bucket=db['bucket_name'])

# #create dynamo db database
dynamo_db = dnamo_database(DynamoDb, db['dynamo_table_name'])
