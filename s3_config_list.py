import os
import boto3
import json

class Config:
    def __init__(self):
        self.cluster_scaling_configs = None

    def read_from_s3(self, bucket, path):
        s3 = boto3.client('s3')
        content_object = s3.get_object(Bucket=bucket, Key=path)
        file_content = content_object['Body'].read().decode('utf-8')
        self.cluster_scaling_configs = json.loads(file_content)
        return self.cluster_scaling_configs

# Get environment variables
environment = os.getenv("ENV", "dev").strip()
bucket = os.getenv("BUCKET_NAME", "dynamic-scaling-lambda-dev-us-east-1").strip()

# Initialize S3 client
s3 = boto3.client('s3')

# List objects in the specified S3 bucket and path
prefix = f'profiles/{environment}/'
response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

# Filter for the first object starting with 'dynamodb'
dynamodb_file = None
for obj in response.get('Contents', []):
    key = obj['Key']
    if key.startswith(prefix + 'dynamodb'):
        dynamodb_file = key
        break

if dynamodb_file:
    config = Config()
    # Read from S3 and print the output
    cluster_scaling_configs = config.read_from_s3(bucket, dynamodb_file)
    
    # Print the output
    print(json.dumps(cluster_scaling_configs, indent=4))
else:
    print("No file starting with 'dynamodb' found in the specified path.")