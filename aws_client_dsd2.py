import json

class AWSClient:  # pragma: no cover
    def __init__(self):
        # Initialize AWS services here (e.g., DynamoDB, Application Auto Scaling, etc.)
        pass

    def creation_table_scaling(self, config):
        min_read_capacity = config['min_read_capacity']
        min_write_capacity = config['min_write_capacity']
        max_read_capacity = config['max_read_capacity']
        max_write_capacity = config['max_write_capacity']
        table_name = config['table_name']
        key_schema = config['key_schema']
        attribute_definitions = config['attribute_definitions']

        table = self.dynamodb.create_table(
            TableName=table_name,
            KeySchema=key_schema,
            AttributeDefinitions=attribute_definitions,
            ProvisionedThroughput={
                'ReadCapacityUnits': min_read_capacity,
                'WriteCapacityUnits': min_write_capacity
            }
        )

        scalable_dimensions = {
            'dynamodb:table:ReadCapacityUnits': [min_read_capacity, max_read_capacity],
            'dynamodb:table:WriteCapacityUnits': [min_write_capacity, max_write_capacity]
        }
        for scalable_dimension, capacity in scalable_dimensions.items():
            self.scaling_dynamodb.register_scalable_target(
                ServiceNamespace="dynamodb",
                ResourceId=f"table/{table_name}",
                ScalableDimension=scalable_dimension,
                MinCapacity=capacity[0],
                MaxCapacity=capacity[1]
            )

        metrics_and_dimension = {
            'DynamoDBReadCapacityUtilization': 'dynamodb:table:ReadCapacityUnits',
            'DynamoDBWriteCapacityUtilization': 'dynamodb:table:WriteCapacityUnits'
        }
        percent_of_use_to_aim_for = config['percent_of_use_to_aim_for']
        scale_out_cooldown_in_seconds = config['scale_out_cooldown_in_seconds']
        scale_in_cooldown_in_seconds = config['scale_in_cooldown_in_seconds']
        for metric, dimension in metrics_and_dimension.items():
            self.scaling_dynamodb.put_scaling_policy(
                ServiceNamespace="dynamodb",
                ResourceId=f"table/{table_name}",
                PolicyType='TargetTrackingScaling',
                PolicyName=f"Scale{metric}",
                ScalableDimension=dimension,
                TargetTrackingScalingPolicyConfiguration={
                    'TargetValue': percent_of_use_to_aim_for,
                    'PredefinedMetricSpecification': {
                        'PredefinedMetricType': metric
                    },
                    'ScaleOutCooldown': scale_out_cooldown_in_seconds,
                    'ScaleInCooldown': scale_in_cooldown_in_seconds
                }
            )
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)