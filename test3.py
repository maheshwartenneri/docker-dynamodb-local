import boto3

class DynamoDBScaler:
    def __init__(self):
        self.dynamodb = boto3.client('dynamodb')
        self.scaling_dynamodb = boto3.client('application-autoscaling')

    def creation_table_scaling(self, config):
        min_read_capacity = config['min_read_capacity']
        min_write_capacity = config['min_write_capacity']
        max_read_capacity = config['max_read_capacity']
        max_write_capacity = config['max_write_capacity']
        table_name = config['table_name']
        key_schema = config['key_schema']
        attribute_definitions = config['attribute_definitions']

        percent_of_use_to_aim_for = config['percent_of_use_to_aim_for']
        scale_out_cooldown_in_seconds = config['scale_out_cooldown_in_seconds']
        scale_in_cooldown_in_seconds = config['scale_in_cooldown_in_seconds']

        # Set scaling policies for read capacity
        self.scaling_dynamodb.put_scaling_policy(
            ServiceNamespace="dynamodb",
            ResourceId=f"table/{table_name}",
            PolicyType='TargetTrackingScaling',
            PolicyName=f"ScaleReadCapacity",
            ScalableDimension='dynamodb:table:ReadCapacityUnits',
            TargetTrackingScalingPolicyConfiguration={
                'TargetValue': percent_of_use_to_aim_for,
                'PredefinedMetricSpecification': {
                    'PredefinedMetricType': 'DynamoDBReadCapacityUtilization'
                },
                'ScaleOutCooldown': scale_out_cooldown_in_seconds,
                'ScaleInCooldown': scale_in_cooldown_in_seconds
            }
        )

        # Set scaling policies for write capacity
        self.scaling_dynamodb.put_scaling_policy(
            ServiceNamespace="dynamodb",
            ResourceId=f"table/{table_name}",
            PolicyType='TargetTrackingScaling',
            PolicyName=f"ScaleWriteCapacity",
            ScalableDimension='dynamodb:table:WriteCapacityUnits',
            TargetTrackingScalingPolicyConfiguration={
                'TargetValue': percent_of_use_to_aim_for,
                'PredefinedMetricSpecification': {
                    'PredefinedMetricType': 'DynamoDBWriteCapacityUtilization'
                },
                'ScaleOutCooldown': scale_out_cooldown_in_seconds,
                'ScaleInCooldown': scale_in_cooldown_in_seconds
            }
        )

        print(f"Scaling policies set for table '{table_name}'.")

        # Update the table capacity back to its original min values
        self.dynamodb.update_table(
            TableName=table_name,
            ProvisionedThroughput={
                'ReadCapacityUnits': min_read_capacity,
                'WriteCapacityUnits': min_write_capacity
            }
        )
        print(f"Table '{table_name}' capacity restored to initial values.")

if __name__ == '__main__':
    # Example configuration
    config = {
        'min_read_capacity': 5,
        'min_write_capacity': 5,
        'max_read_capacity': 100,
        'max_write_capacity': 100,
        'table_name': 'YourTableName',
        'key_schema': [
            {
                'AttributeName': 'YourPrimaryKey',
                'KeyType': 'HASH'
            }
        ],
        'attribute_definitions': [
            {
                'AttributeName': 'YourPrimaryKey',
                'AttributeType': 'S'
            }
        ],
        'percent_of_use_to_aim_for': 70.0,
        'scale_out_cooldown_in_seconds': 60,
        'scale_in_cooldown_in_seconds': 60
    }

    scaler = DynamoDBScaler()
    scaler.creation_table_scaling(config)