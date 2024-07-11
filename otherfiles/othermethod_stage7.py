def read_from_s3(self, bucket, path):
    content_object = s3.Object(bucket, path)
    file_content = content_object.get()['Body'].read().decode('utf-8')
    self.cluster_scaling_configs = json.loads(file_content)

def update_scaling_policies(self, aws_region_client, table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity):
    try:
        aws_region_client.register_scalable_target(
            ServiceNamespace='dynamodb',
            ResourceId=f'table/{table_name}',
            ScalableDimension='dynamodb:table:ReadCapacityUnits',
            MinCapacity=min_read_capacity,
            MaxCapacity=max_read_capacity
        )
        aws_region_client.register_scalable_target(
            ServiceNamespace='dynamodb',
            ResourceId=f'table/{table_name}',
            ScalableDimension='dynamodb:table:WriteCapacityUnits',
            MinCapacity=min_write_capacity,
            MaxCapacity=max_write_capacity
        )
        print(f"Auto-scaling settings for {table_name} updated successfully in {aws_region_client.meta.region_name}.")
        print(f"Read Capacity Range: {min_read_capacity} - {max_read_capacity}")
        print(f"Write Capacity Range: {min_write_capacity} - {max_write_capacity}")
    except Exception as e:
        print(f"Error updating auto-scaling for {table_name} in {aws_region_client.meta.region_name}: {e}")

def scale_out_dynamodb(self, region):
    aws_region_client = boto3.client('application-autoscaling', region_name=region)
    for table_config in self.cluster_scaling_configs['tables']:
        table_name = table_config['table_name']
        min_read_capacity = table_config['scale_out_min_read_capacity']
        max_read_capacity = table_config['scale_out_max_read_capacity']
        min_write_capacity = table_config['scale_out_min_write_capacity']
        max_write_capacity = table_config['scale_out_max_write_capacity']
        self.update_scaling_policies(aws_region_client, table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity)

def scale_in_dynamodb(self, region):
    aws_region_client = boto3.client('application-autoscaling', region_name=region)
    for table_config in self.cluster_scaling_configs['tables']:
        table_name = table_config['table_name']
        min_read_capacity = table_config['scale_in_min_read_capacity']
        max_read_capacity = table_config['scale_in_max_read_capacity']
        min_write_capacity = table_config['scale_in_min_write_capacity']
        max_write_capacity = table_config['scale_in_max_write_capacity']
        self.update_scaling_policies(aws_region_client, table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity)

def main(json_file_path, scale_direction):
    scaler = DynamoDBScaler()
    scaler.read_from_s3('my-bucket', json_file_path)

    if scale_direction == "out":
        scaler.scale_out_dynamodb('us-east-1')
        scaler.scale_out_dynamodb('us-west-2')
    elif scale_direction == "in":
        scaler.scale_in_dynamodb('us-east-1')
        scaler.scale_in_dynamodb('us-west-2')

# Set these variables with your specific values
json_file_path = 'applications/Github/Boto3_Local_Testing/scalerout.env.json'
scale_direction = 'out'  # or 'in'

main(json_file_path, scale_direction)