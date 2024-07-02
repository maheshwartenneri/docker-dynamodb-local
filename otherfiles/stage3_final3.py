import boto3
import json

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

def scale_in_dynamodb(table_config):
    table_name = table_config['table_name']
    min_read_capacity = table_config['original_min_read_capacity']
    max_read_capacity = table_config['original_max_read_capacity']
    min_write_capacity = table_config['original_min_write_capacity']
    max_write_capacity = table_config['original_max_write_capacity']
    
    update_scaling_policies(table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity)

def scale_out_dynamodb(table_config):
    table_name = table_config['table_name']
    min_read_capacity = table_config['min_read_capacity']
    max_read_capacity = table_config['max_read_capacity']
    min_write_capacity = table_config['min_write_capacity']
    max_write_capacity = table_config['max_write_capacity']
    
    update_scaling_policies(table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity)

def main(scale_type):
    # Load configuration from env.json
    with open('/Users/ekp945/Documents/GitHub/Boto3_Local_testing/dynamodb.envprofile.dev.json', 'r') as file:
        config = json.load(file)
        
    for table_config in config['tables']:
        if scale_type == 'scaleout':
            scale_out_dynamodb(table_config)
        elif scale_type == 'scalein':
            scale_in_dynamodb(table_config)
        else:
            print(f"Invalid scale type: {scale_type}")
            return

if __name__ == "__main__":
    scale_type = 'scaleout'  # Change to 'scalein' to update to original values
    main(scale_type)