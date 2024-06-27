import boto3

def update_table_capacity(table_name, read_capacity, write_capacity):
    try:
        # Initialize the DynamoDB client
        dynamodb = boto3.client("dynamodb", region_name="us-east-1")
        
        # Update the table's provisioned throughput
        dynamodb.update_table(
            TableName=table_name,
            ProvisionedThroughput={
                'ReadCapacityUnits': read_capacity,
                'WriteCapacityUnits': write_capacity
            }
        )
        
        # Wait until the table is updated
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        
        print(f"Table '{table_name}' provisioned capacity updated successfully.")
        print(f"New Read Capacity: {read_capacity}")
        print(f"New Write Capacity: {write_capacity}")
    
    except Exception as e:
        print(f"Error updating table capacity '{table_name}': {e}")

def update_scaling_policies(table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity):
    try:
        # Initialize the Application Auto Scaling client
        autoscaling = boto3.client('application-autoscaling', region_name='us-east-1')
        
        # Update scalable target for read capacity
        autoscaling.register_scalable_target(
            ServiceNamespace='dynamodb',
            ResourceId=f'table/{table_name}',
            ScalableDimension='dynamodb:table:ReadCapacityUnits',
            MinCapacity=min_read_capacity,
            MaxCapacity=max_read_capacity
        )
        
        # Update scalable target for write capacity
        autoscaling.register_scalable_target(
            ServiceNamespace='dynamodb',
            ResourceId=f'table/{table_name}',
            ScalableDimension='dynamodb:table:WriteCapacityUnits',
            MinCapacity=min_write_capacity,
            MaxCapacity=max_write_capacity
        )
        
        print(f"Auto-scaling settings for '{table_name}' updated successfully.")
        print(f"Read Capacity Range: {min_read_capacity} - {max_read_capacity}")
        print(f"Write Capacity Range: {min_write_capacity} - {max_write_capacity}")
    
    except Exception as e:
        print(f"Error updating auto-scaling settings for '{table_name}': {e}")

def main():
    table_name = "dev_ledger_instrument_versions"
    read_capacity = 15  # New read capacity
    write_capacity = 2  # New write capacity
    min_read_capacity = 5  # Minimum read capacity
    max_read_capacity = 20  # Maximum read capacity
    min_write_capacity = 1  # Minimum write capacity
    max_write_capacity = 10  # Maximum write capacity
    
    # Update the table's provisioned throughput
    update_table_capacity(table_name, read_capacity, write_capacity)
    
    # Update auto-scaling settings
    update_scaling_policies(table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity)

if __name__ == "__main__":
    main()