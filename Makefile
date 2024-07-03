# A make file that automates the process

all: s3_DynamoDb_Role bucketPolicy vPC_EC2 loadBalancer_targetGroup autoScalingGroup

s3_DynamoDb_Role:
	python create_role_db_s3.py

bucketPolicy:
	python s3_bucket_policy.py

vPC_EC2:
	python create_vpc_network_ec2.py

loadBalancer_targetGroup:
	python create_load_balancer.py

autoScalingGroup:
	python create_auto_scaling_group.py

clean:
	python cleanup.py

