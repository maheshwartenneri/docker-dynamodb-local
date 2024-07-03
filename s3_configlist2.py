import os
import boto3
import json

class Config:
    def __init__(self):
        self.cluster_scaling_configs = {}

    def read_from_s3(self, bucket, path):
        s3 = boto3.client('s3')
        content_object = s3.get_object(Bucket=bucket, Key=path)
        file_content = content_object['Body'].read().decode('utf-8')
        return json.loads(file_content)

# Get environment variables
environment = os.getenv("ENV", "dev").strip()
bucket = os.getenv("BUCKET_NAME", "dynamic-scaling-lambda-dev-us-east-1").strip()

# Initialize S3 client
s3 = boto3.client('s3')

# List objects in the specified S3 bucket and path
prefix = f'profiles/{environment}/'
response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

config = Config()

# Iterate over all objects and read their contents
if 'Contents' in response:
    for obj in response['Contents']:
        key = obj['Key']
        file_content = config.read_from_s3(bucket, key)
        config.cluster_scaling_configs[key] = file_content

    # Print all configurations
    print(json.dumps(config.cluster_scaling_configs, indent=4))
else:
    print("No objects found in the specified path.")