def test_creation_table_scaling(self):
    config = {
        'min_read_capacity': 5,
        'min_write_capacity': 5,
        'max_read_capacity': 100,
        'max_write_capacity': 100,
        'table_name': 'test-table',
        'key_schema': [
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        'attribute_definitions': [
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            }
        ],
        'percent_of_use_to_aim_for': 70,
        'scale_out_cooldown_in_seconds': 60,
        'scale_in_cooldown_in_seconds': 60
    }

    dynamodb_mock = Mock()
    scaling_dynamodb_mock = Mock()

    table_mock = Mock()
    table_meta_mock = Mock()
    waiter_mock = Mock()

    dynamodb_mock.create_table.return_value = table_mock
    table_mock.meta.client.get_waiter.return_value = waiter_mock

    dynamic_scaling_controller.aws_client.dynamodb = dynamodb_mock
    dynamic_scaling_controller.aws_client.scaling_dynamodb = scaling_dynamodb_mock

    dynamic_scaling_controller.aws_client.creation_table_scaling(config)

    dynamodb_mock.create_table.assert_called_with(
        TableName='test-table',
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    waiter_mock.wait.assert_called_with(TableName='test-table')
    dynamodb_mock.update_table.assert_called_with(
        TableName='test-table',
        ProvisionedThroughput={
            'ReadCapacityUnits': 100,
            'WriteCapacityUnits': 100
        }
    )
    scaling_dynamodb_mock.put_scaling_policy.assert_any_call(
        ServiceNamespace="dynamodb",
        ResourceId="table/test-table",
        PolicyType='TargetTrackingScaling',
        PolicyName="ScaleDynamoDBReadCapacityUtilization",
        ScalableDimension='dynamodb:table:ReadCapacityUnits',
        TargetTrackingScalingPolicyConfiguration={
            'TargetValue': 70,
            'PredefinedMetricSpecification': {
                'PredefinedMetricType': 'DynamoDBReadCapacityUtilization'
            },
            'ScaleOutCooldown': 60,
            'ScaleInCooldown': 60
        }
    )
    scaling_dynamodb_mock.put_scaling_policy.assert_any_call(
        ServiceNamespace="dynamodb",
        ResourceId="table/test-table",
        PolicyType='TargetTrackingScaling',
        PolicyName="ScaleDynamoDBWriteCapacityUtilization",
        ScalableDimension='dynamodb:table:WriteCapacityUnits',
        TargetTrackingScalingPolicyConfiguration={
            'TargetValue': 70,
            'PredefinedMetricSpecification': {
                'PredefinedMetricType': 'DynamoDBWriteCapacityUtilization'
            },
            'ScaleOutCooldown': 60,
            'ScaleInCooldown': 60
        }
    )
    dynamodb_mock.update_table.assert_called_with(
        TableName='test-table',
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )