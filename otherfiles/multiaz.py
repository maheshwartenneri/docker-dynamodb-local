import boto3
import json

class DynamoDBScaler:

    def __init__(self):
        self.east_application_autoscaling = boto3.client('application-autoscaling', region_name='us-east-1')
        self.west_application_autoscaling = boto3.client('application-autoscaling', region_name='us-west-2')

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

    def scale_out_dynamodb(self):
        print("Scaling out DynamoDb capacity...")
        for table_config in self.cluster_scaling_configs['tables']:
            table_name = table_config['table_name']
            min_read_capacity = table_config['scale_out_min_read_capacity']
            max_read_capacity = table_config['scale_out_max_read_capacity']
            min_write_capacity = table_config['scale_out_min_write_capacity']
            max_write_capacity = table_config['scale_out_max_write_capacity']

            self.update_scaling_policies(self.east_application_autoscaling, table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity)
            self.update_scaling_policies(self.west_application_autoscaling, table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity)
        print("DynamoDb capacity scale-out complete")

    def scale_in_dynamodb(self):
        print("Scaling in DynamoDb capacity...")
        for table_config in self.cluster_scaling_configs['tables']:
            table_name = table_config['table_name']
            min_read_capacity = table_config['scale_in_min_read_capacity']
            max_read_capacity = table_config['scale_in_max_read_capacity']
            min_write_capacity = table_config['scale_in_min_write_capacity']
            max_write_capacity = table_config['scale_in_max_write_capacity']

            self.update_scaling_policies(self.east_application_autoscaling, table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity)
            self.update_scaling_policies(self.west_application_autoscaling, table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity)
        print("DynamoDb capacity scale-in complete")

def main(json_file_path, scale_direction):
    scaler = DynamoDBScaler()
    scaler.read_from_json(json_file_path)

    if scale_direction == "out":
        scaler.scale_out_dynamodb()
    elif scale_direction == "in":
        scaler.scale_in_dynamodb()

if __name__ == "__main__":
    # Set these variables with your specific values
    json_file_path = 'path/to/your/env.json'
    scale_direction = 'out'  # or 'in'

    main(json_file_path, scale_direction)