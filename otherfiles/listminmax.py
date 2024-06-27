import boto3

def list_table_capacity(table_name):
    try:
        # Initialize the DynamoDB client
        dynamodb = boto3.client("dynamodb", region_name="us-east-1")
        
        # Describe the table to get its current capacities
        response = dynamodb.describe_table(TableName=table_name)
        table_description = response['Table']
        
        read_capacity = table_description['ProvisionedThroughput']['ReadCapacityUnits']
        write_capacity = table_description['ProvisionedThroughput']['WriteCapacityUnits']
        
        print(f"Table '{table_name}' current capacity:")
        print(f"Read Capacity: {read_capacity}")
        print(f"Write Capacity: {write_capacity}")
        
        # Initialize the Application Auto Scaling client
        autoscaling = boto3.client('application-autoscaling', region_name='us-east-1')
        
        # List scalable targets for the table
        scalable_targets = autoscaling.describe_scalable_targets(
            ServiceNamespace='dynamodb',
            ResourceIds=[f'table/{table_name}']
        )
        
        min_read_capacity = None
        max_read_capacity = None
        min_write_capacity = None
        max_write_capacity = None
        
        for target in scalable_targets['ScalableTargets']:
            if target['ScalableDimension'] == 'dynamodb:table:ReadCapacityUnits':
                min_read_capacity = target['MinCapacity']
                max_read_capacity = target['MaxCapacity']
            elif target['ScalableDimension'] == 'dynamodb:table:WriteCapacityUnits':
                min_write_capacity = target['MinCapacity']
                max_write_capacity = target['MaxCapacity']
        
        if min_read_capacity is not None and max_read_capacity is not None:
            print(f"Read Capacity Range: {min_read_capacity} - {max_read_capacity}")
        else:
            print("Read Capacity Range: Not configured for auto-scaling")
        
        if min_write_capacity is not None and max_write_capacity is not None:
            print(f"Write Capacity Range: {min_write_capacity} - {max_write_capacity}")
        else:
            print("Write Capacity Range: Not configured for auto-scaling")
    
    except Exception as e:
        print(f"Error describing table '{table_name}': {e}")

if __name__ == "__main__":
    table_name = "dev_ledger_instrument_versions"
    list_table_capacity(table_name)