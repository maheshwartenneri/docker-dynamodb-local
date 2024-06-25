import boto3

class AWSClient:
    def __init__(self):
        # Initialize the DynamoDB client with the specified region
        self.dynamodb = boto3.client('dynamodb', region_name='us-east-1')

    def update_table_capacity(self, config):
        table_name = config['table_name']
        read_capacity = config['read_capacity']
        write_capacity = config['write_capacity']

        try:
            # Update the table's provisioned throughput
            response = self.dynamodb.update_table(
                TableName=table_name,
                ProvisionedThroughput={
                    'ReadCapacityUnits': read_capacity,
                    'WriteCapacityUnits': write_capacity
                }
            )

            # Wait until the table is updated
            waiter = self.dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=table_name)

            print(f"Table '{table_name}' updated successfully.")
            print(f"New Read Capacity: {read_capacity}")
            print(f"New Write Capacity: {write_capacity}")
        
        except Exception as e:
            print(f"Error updating table '{table_name}': {e}")

if __name__ == "__main__":
    config = {
        "table_name": "dev_ledger_instrument_versions",
        "read_capacity": 20,
        "write_capacity": 2
    }

    aws_client = AWSClient()
    aws_client.update_table_capacity(config)
