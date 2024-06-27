import boto3

def update_table_capacity(table_name, read_capacity, write_capacity, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity):
    try:
        # Initialize the DynamoDB client
        dynamodb = boto3.client("dynamodb", region_name="us-east-1")
        
        # Update the table's provisioned throughput
        response = dynamodb.update_table(
            TableName=table_name,
            ProvisionedThroughput={
                'ReadCapacityUnits': read_capacity,
                'WriteCapacityUnits': write_capacity
            }
        )
        
        # Wait until the table is updated
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        
        print(f"Table '{table_name}' capacity updated successfully.")
        print(f"New Read Capacity: {read_capacity}")
        print(f"New Write Capacity: {write_capacity}")
        print(f"Read Capacity Range: {min_read_capacity} - {max_read_capacity}")
        print(f"Write Capacity Range: {min_write_capacity} - {max_write_capacity}")
    
    except Exception as e:
        print(f"Error updating table capacity '{table_name}': {e}")

if __name__ == "__main__":
    table_name = "dev_ledger_instrument_versions"
    read_capacity = 15  # New read capacity
    write_capacity = 2  # New write capacity
    min_read_capacity = 5  # Minimum read capacity
    max_read_capacity = 20  # Maximum read capacity
    min_write_capacity = 1  # Minimum write capacity
    max_write_capacity = 10  # Maximum write capacity
    
    update_table_capacity(table_name, read_capacity, write_capacity, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity)