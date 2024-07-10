import boto3
import json

class DynamoDBScaler:

    def __init__(self):
        self.clients = {
            'us-east-1': boto3.client('application-autoscaling', region_name='us-east-1'),
            'us-west-2': boto3.client('application-autoscaling', region_name='us-west-2')
        }
        self.cluster_scaling_configs = None  # Initialize to None until loaded

    def read_from_json(self, file_path):
        with open(file_path, 'r') as file:
            self.cluster_scaling_configs = json.load(file)

    def update_scaling_policies(self, aws_region_client, table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity):
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
            print(f"Auto-scaling settings for {table_name} updated successfully in {aws_region_client.meta.region_name}.")
            print(f"Read Capacity Range: {min_read_capacity} - {max_read_capacity}")
            print(f"Write Capacity Range: {min_write_capacity} - {max_write_capacity}")
        except Exception as e:
            print(f"Error updating auto-scaling settings for {table_name} in {aws_region_client.meta.region_name}: {e}")

    def scale_out_dynamodb(self, region):
        if self.cluster_scaling_configs is None:
            raise ValueError("Cluster scaling configurations not loaded. Call read_from_json first.")

        print(f"Scaling out DynamoDb capacity in {region}...")
        for table_config in self.cluster_scaling_configs['tables']:
            table_name = table_config['table_name']
            min_read_capacity = table_config['scale_out_min_read_capacity']
            max_read_capacity = table_config['scale_out_max_read_capacity']
            min_write_capacity = table_config['scale_out_min_write_capacity']
            max_write_capacity = table_config['scale_out_max_write_capacity']

            aws_region_client = self.clients[region]
            self.update_scaling_policies(aws_region_client, table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity)
        print(f"DynamoDb capacity scale-out complete in {region}")

    def scale_in_dynamodb(self, region):
        if self.cluster_scaling_configs is None:
            raise ValueError("Cluster scaling configurations not loaded. Call read_from_json first.")

        print(f"Scaling in DynamoDb capacity in {region}...")
        for table_config in self.cluster_scaling_configs['tables']:
            table_name = table_config['table_name']
            min_read_capacity = table_config['scale_in_min_read_capacity']
            max_read_capacity = table_config['scale_in_max_read_capacity']
            min_write_capacity = table_config['scale_in_min_write_capacity']
            max_write_capacity = table_config['scale_in_max_write_capacity']

            aws_region_client = self.clients[region]
            self.update_scaling_policies(aws_region_client, table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity)
        print(f"DynamoDb capacity scale-in complete in {region}")

def main(json_file_path, scale_direction):
    scaler = DynamoDBScaler()
    scaler.read_from_json(json_file_path)

    if scale_direction == "out":
        scaler.scale_out_dynamodb('us-east-1')
        scaler.scale_out_dynamodb('us-west-2')
    elif scale_direction == "in":
        scaler.scale_in_dynamodb('us-east-1')
        scaler.scale_in_dynamodb('us-west-2')

if __name__ == "__main__":
    # Set these variables with your specific values
    json_file_path = 'path/to/your/env.json'
    scale_direction = 'out'  # or 'in'

    main(json_file_path, scale_direction)