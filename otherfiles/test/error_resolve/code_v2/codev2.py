To modify the function to avoid the "None type object has no attribute ‘cluster_scaling_configs’" error, you need to ensure that the `Config` object is properly instantiated and `cluster_scaling_configs` is not `None`. Here is an example of how you can achieve this:

1. **Check for None**: Add a check to ensure that `Config` is properly instantiated and `cluster_scaling_configs` is not `None`.
2. **Error Handling**: Implement error handling to provide a meaningful message if `Config` is not properly set up.

Here's the modified version of the function:

```python
class AWSClient:
    def __init__(self):
        self.east_application_autoscaling = boto3.client('application-autoscaling', region_name='us-east-1')
        self.west_application_autoscaling = boto3.client('application-autoscaling', region_name='us-west-2')

    def update_scaling_policies(self, aws_region_client, table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity):
        try:
            # Update scalable target for read capacity
            aws_region_client.register_scalable_target(
                ServiceNamespace='dynamodb',
                ResourceId='table/' + table_name,
                ScalableDimension='dynamodb:table:ReadCapacityUnits',
                MinCapacity=min_read_capacity,
                MaxCapacity=max_read_capacity
            )

            # Update scalable target for write capacity
            aws_region_client.register_scalable_target(
                ServiceNamespace='dynamodb',
                ResourceId='table/' + table_name,
                ScalableDimension='dynamodb:table:WriteCapacityUnits',
                MinCapacity=min_write_capacity,
                MaxCapacity=max_write_capacity
            )
            print(f"Auto-scaling settings for {table_name} updated successfully in {aws_region_client.meta.region_name}.")
            print(f"Read Capacity Range: {min_read_capacity} - {max_read_capacity}")
            print(f"Write Capacity Range: {min_write_capacity} - {max_write_capacity}")
        except Exception as e:
            print(f"Error updating auto-scaling settings for {table_name} in {aws_region_client.meta.region_name}: {e}")

def scale_out_dynamodb(region):
    aws_region_client = boto3.client('application-autoscaling', region_name=region)
    table_config = Config.cluster_scaling_configs['tables'] if Config and Config.cluster_scaling_configs else None
    if not table_config:
        raise ValueError("Invalid configuration: 'cluster_scaling_configs' is missing or 'tables' key is not found")

    table_name = table_config['table_name']
    min_read_capacity = table_config['scale_out_min_read_capacity']
    max_read_capacity = table_config['scale_out_max_read_capacity']
    min_write_capacity = table_config['scale_out_min_write_capacity']
    max_write_capacity = table_config['scale_out_max_write_capacity']

    aws_client.update_scaling_policies(aws_region_client, table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity)

def scale_in_dynamodb(region):
    aws_region_client = boto3.client('application-autoscaling', region_name=region)
    table_config = Config.cluster_scaling_configs['tables'] if Config and Config.cluster_scaling_configs else None
    if not table_config:
        raise ValueError("Invalid configuration: 'cluster_scaling_configs' is missing or 'tables' key is not found")

    table_name = table_config['table_name']
    min_read_capacity = table_config['scale_in_min_read_capacity']
    max_read_capacity = table_config['scale_in_max_read_capacity']
    min_write_capacity = table_config['scale_in_min_write_capacity']
    max_write_capacity = table_config['scale_in_max_write_capacity']

    aws_client.update_scaling_policies(aws_region_client, table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity)

def lambda_handler(event, context):
    if not event:
        return {
            "body": {"status": "failure"},
            "statusCode": 400,
        }
    
    config = Config(event)
    environment = os.getenv("ENV", "dev").strip()
    bucket = os.getenv("BUCKET_NAME", "dynamic-scaling-lambda-dev-us-east-1").strip()
    path = f"profiles/{environment}/{config.profile}"

    config.read_from_s3(bucket, path)
    
    if config.scale == "out":
        if config.resource == "dynamodb":
            print(f"Scaling out in DynamoDB capacity in {region}...")
            scale_out_dynamodb('us-east-1')
            scale_out_dynamodb('us-west-2')
            print("DynamoDB capacity scale out complete")
    elif config.scale == "in":
        if config.resource == "dynamodb":
            print(f"Scaling in DynamoDB capacity in {region}...")
            scale_in_dynamodb('us-east-1')
            scale_in_dynamodb('us-west-2')
            print("DynamoDB capacity scale in complete")
    else:
        raise ValueError(f"Invalid parameter, event: {event}")
```

In this modified code:
- I added checks to ensure that `Config` is instantiated and `cluster_scaling_configs` is not `None`.
- If `Config` is `None` or `cluster_scaling_configs` is missing, the function will raise a `ValueError` with an appropriate message.

This should prevent the `NoneType` error and provide a more robust and clear handling of missing configurations.