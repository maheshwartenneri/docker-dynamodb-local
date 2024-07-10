def read_from_s3(self, bucket, path):
    content_object = s3.Object(bucket, path)
    file_content = content_object.get()['Body'].read().decode('utf-8')
    self.cluster_scaling_configs = json.loads(file_content)

def update_scaling_policies(region_name, table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity):
    if region_name == 'us-east-1':
        aws_region_client = self.east_application_autoscaling
    elif region_name == 'us-west-2':
        aws_region_client = self.west_application_autoscaling
    else:
        raise ValueError(f'Unsupported region: {region_name}')
    try:
        # Update scalable target for read capacity
        aws_region_client.register_scalable_target(
            ServiceNamespace='dynamodb',
            ResourceId=f'table/{table_name}',
            ScalableDimension='dynamodb:table:ReadCapacityUnits',
            MinCapacity=min_read_capacity,
            MaxCapacity=max_read_capacity
        )
        # Update scalable target for write capacity
        aws_region_client.register_scalable_target(
            ServiceNamespace='dynamodb',
            ResourceId=f'table/{table_name}',
            ScalableDimension='dynamodb:table:WriteCapacityUnits',
            MinCapacity=min_write_capacity,
            MaxCapacity=max_write_capacity
        )
        print(f"Auto-scaling settings for {table_name} updated successfully.")
        print(f"Read Capacity Range: {min_read_capacity} - {max_read_capacity}")
        print(f"Write Capacity Range: {min_write_capacity} - {max_write_capacity}")
    except Exception as e:
        print(f"Error updating auto-scaling settings for {table_name}: {e}")

def scale_out_dynamodb(region_name, table_config):
    table_name = table_config['table_name']
    min_read_capacity = table_config['scale_out_min_read_capacity']
    max_read_capacity = table_config['scale_out_max_read_capacity']
    min_write_capacity = table_config['scale_out_min_write_capacity']
    max_write_capacity = table_config['scale_out_max_write_capacity']
    update_scaling_policies(table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity)

def scale_in_dynamodb(region_name, table_config):
    table_name = table_config['table_name']
    min_read_capacity = table_config['scale_in_min_read_capacity']
    max_read_capacity = table_config['scale_in_max_read_capacity']
    min_write_capacity = table_config['scale_in_min_write_capacity']
    max_write_capacity = table_config['scale_in_max_write_capacity']
    update_scaling_policies(table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity)

def main():
    if config.scale == "out":
        print("Scaling out DynamoDb capacity...")
        scale_out_dynamodb()
        print("DynamoDb capacity Scale out complete")
    elif config.scale == "in":
        print("Scaling in DynamoDb capacity...")
        scale_in_dynamodb()
        print("DynamoDb capacity Scale in complete")

main()