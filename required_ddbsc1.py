def creation_table_scaling(self, config):
    min_read_capacity = config['min_read_capacity']
    min_write_capacity = config['min_write_capacity']
    max_read_capacity = config['max_read_capacity']
    max_write_capacity = config['max_write_capacity']
    table_name = config['table_name']
    key_schema = config['key_schema']
    attribute_definitions = config['attribute_definitions']

    # Create DynamoDB table with initial capacity
    table = self.dynamodb.create_table(
        TableName=table_name,
        KeySchema=key_schema,
        AttributeDefinitions=attribute_definitions,
        ProvisionedThroughput={
            'ReadCapacityUnits': min_read_capacity,
            'WriteCapacityUnits': min_write_capacity
        }
    )

    # Wait until the table exists
    table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
    print(f"Table '{table_name}' created successfully.")

    # Increase the table capacity to the desired max values
    self.dynamodb.update_table(
        TableName=table_name,
        ProvisionedThroughput={
            'ReadCapacityUnits': max_read_capacity,
            'WriteCapacityUnits': max_write_capacity
        }
    )
    print(f"Table '{table_name}' updated to max capacity successfully.")

    # Set scaling policies for read and write capacities
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
