```python
import unittest
from unittest.mock import patch, Mock

class TestDynamoDBScaling(unittest.TestCase):

    def update_scaling_policies(self, region_name, table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity):
        if region_name == 'us-east-1':
            aws_region_client = self.east_application_autoscaling
        elif region_name == "us-west-2":
            aws_region_client = self.west_application_autoscaling
        else:
            raise ValueError(f'Unsupported region: {region_name}')
        try:
            # Update scalable target for read capacity
            aws_region_client.register_scalable_target(
                ServiceNamespace='dynamodb',
                ResourceId=f'table/{table_name}',
                ScalableDimension='dynamodb:table:ReadCapacityUnits',
                MinCapacity=min_read_capacity, MaxCapacity=max_read_capacity
            )
            # Update scalable target for write capacity
            aws_region_client.register_scalable_target(
                ServiceNamespace='dynamodb',
                ResourceId=f'table/{table_name}',
                ScalableDimension='dynamodb:table:WriteCapacityUnits',
                MinCapacity=min_write_capacity, MaxCapacity=max_write_capacity
            )
            print(f"Auto-scaling settings for '{table_name}' updated successfully.")
            print(f"Read Capacity Ranges {min_read_capacity} - {max_read_capacity}")
            print(f"Write Capacity Ranges {min_write_capacity} - {max_write_capacity}")
        except Exception as e:
            print(f"Error updating auto-scaling settings for '{table_name}', {e}")

    def scale_out_dynamodb(self, region_name, table_config):
        table_name = table_config['table_name']
        min_read_capacity = table_config['scale_out_min_read_capacity']
        max_read_capacity = table_config['scale_out_max_read_capacity']
        min_write_capacity = table_config['scale_out_min_write_capacity']
        max_write_capacity = table_config['scale_out_max_write_capacity']
        self.update_scaling_policies(region_name, table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity)

    def scale_in_dynamodb(self, region_name, table_config):
        table_name = table_config['table_name']
        min_read_capacity = table_config['scale_in_min_read_capacity']
        max_read_capacity = table_config['scale_in_max_read_capacity']
        min_write_capacity = table_config['scale_in_min_write_capacity']
        max_write_capacity = table_config['scale_in_max_write_capacity']
        self.update_scaling_policies(region_name, table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity)

    @patch('dynamic_scaling_controller.DynamoDBClient')
    def test_update_scaling_policies(self, MockDynamoDBClient):
        mock_client = MockDynamoDBClient.return_value
        mock_client.register_scalable_target.return_value = {}

        self.update_scaling_policies('us-east-1', 'test-table', 1, 10, 1, 5)

        mock_client.register_scalable_target.assert_any_call(
            ServiceNamespace='dynamodb',
            ResourceId='table/test-table',
            ScalableDimension='dynamodb:table:ReadCapacityUnits',
            MinCapacity=1, MaxCapacity=10
        )

        mock_client.register_scalable_target.assert_any_call(
            ServiceNamespace='dynamodb',
            ResourceId='table/test-table',
            ScalableDimension='dynamodb:table:WriteCapacityUnits',
            MinCapacity=1, MaxCapacity=5
        )

    @patch('dynamic_scaling_controller.DynamoDBClient')
    def test_scale_out_dynamodb(self, MockDynamoDBClient):
        mock_client = MockDynamoDBClient.return_value
        mock_client.register_scalable_target.return_value = {}

        table_config = {
            'table_name': 'test-table',
            'scale_out_min_read_capacity': 1,
            'scale_out_max_read_capacity': 10,
            'scale_out_min_write_capacity': 1,
            'scale_out_max_write_capacity': 5
        }

        self.scale_out_dynamodb('us-east-1', table_config)

        mock_client.register_scalable_target.assert_any_call(
            ServiceNamespace='dynamodb',
            ResourceId='table/test-table',
            ScalableDimension='dynamodb:table:ReadCapacityUnits',
            MinCapacity=1, MaxCapacity=10
        )

        mock_client.register_scalable_target.assert_any_call(
            ServiceNamespace='dynamodb',
            ResourceId='table/test-table',
            ScalableDimension='dynamodb:table:WriteCapacityUnits',
            MinCapacity=1, MaxCapacity=5
        )

    @patch('dynamic_scaling_controller.DynamoDBClient')
    def test_scale_in_dynamodb(self, MockDynamoDBClient):
        mock_client = MockDynamoDBClient.return_value
        mock_client.register_scalable_target.return_value = {}

        table_config = {
            'table_name': 'test-table',
            'scale_in_min_read_capacity': 1,
            'scale_in_max_read_capacity': 10,
            'scale_in_min_write_capacity': 1,
            'scale_in_max_write_capacity': 5
        }

        self.scale_in_dynamodb('us-east-1', table_config)

        mock_client.register_scalable_target.assert_any_call(
            ServiceNamespace='dynamodb',
            ResourceId='table/test-table',
            ScalableDimension='dynamodb:table:ReadCapacityUnits',
            MinCapacity=1, MaxCapacity=10
        )

        mock_client.register_scalable_target.assert_any_call(
            ServiceNamespace='dynamodb',
            ResourceId='table/test-table',
            ScalableDimension='dynamodb:table:WriteCapacityUnits',
            MinCapacity=1, MaxCapacity=5
        )

if __name__ == '__main__':
    unittest.main()
```

This test suite includes three tests:

1. `test_update_scaling_policies`: Tests the `update_scaling_policies` method.
2. `test_scale_out_dynamodb`: Tests the `scale_out_dynamodb` method.
3. `test_scale_in_dynamodb`: Tests the `scale_in_dynamodb` method.

Each test uses the `unittest.mock.patch` decorator to mock the `DynamoDBClient`, ensuring that your tests do not make actual calls to AWS services.