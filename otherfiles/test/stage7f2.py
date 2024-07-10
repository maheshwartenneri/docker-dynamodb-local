import unittest
from unittest.mock import patch, Mock
import json

# Assuming the module name is dynamodb_scaling_controller
import dynamodb_scaling_controller

class TestDynamoDBScalingController(unittest.TestCase):

    def setUp(self):
        self.scaler = dynamodb_scaling_controller.DynamoDBScaler()
        self.table_config = {
            'table_name': 'test_table',
            'scale_out_min_read_capacity': 1,
            'scale_out_max_read_capacity': 5,
            'scale_out_min_write_capacity': 1,
            'scale_out_max_write_capacity': 5,
            'scale_in_min_read_capacity': 1,
            'scale_in_max_read_capacity': 5,
            'scale_in_min_write_capacity': 1,
            'scale_in_max_write_capacity': 5
        }

    @patch('dynamodb_scaling_controller.boto3.resource')
    def test_read_from_s3(self, mock_boto_resource):
        mock_s3 = Mock()
        mock_object = Mock()
        mock_object.get.return_value = {'Body': Mock(read=Mock(return_value=b'{"tables": []}'))}
        mock_s3.Object.return_value = mock_object
        mock_boto_resource.return_value = mock_s3

        self.scaler.read_from_s3('bucket', 'path')
        self.assertEqual(self.scaler.cluster_scaling_configs, {"tables": []})
        mock_s3.Object.assert_called_with('bucket', 'path')
        mock_object.get.assert_called()

    @patch('dynamodb_scaling_controller.boto3.client')
    def test_update_scaling_policies(self, mock_boto_client):
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        mock_client.register_scalable_target.return_value = {}

        self.scaler.update_scaling_policies('us-east-1', 'test_table', 1, 5, 1, 5)
        
        calls = [
            patch.call(ServiceNamespace='dynamodb', ResourceId='table/test_table', ScalableDimension='dynamodb:table:ReadCapacityUnits', MinCapacity=1, MaxCapacity=5),
            patch.call(ServiceNamespace='dynamodb', ResourceId='table/test_table', ScalableDimension='dynamodb:table:WriteCapacityUnits', MinCapacity=1, MaxCapacity=5)
        ]
        mock_client.register_scalable_target.assert_has_calls(calls, any_order=True)

    @patch.object(dynamodb_scaling_controller.DynamoDBScaler, 'update_scaling_policies')
    def test_scale_out_dynamodb(self, mock_update_scaling_policies):
        self.scaler.scale_out_dynamodb('us-east-1', self.table_config)
        self.assertTrue(mock_update_scaling_policies.called)
        mock_update_scaling_policies.assert_called_with('test_table', 1, 5, 1, 5)

    @patch.object(dynamodb_scaling_controller.DynamoDBScaler, 'update_scaling_policies')
    def test_scale_in_dynamodb(self, mock_update_scaling_policies):
        self.scaler.scale_in_dynamodb('us-east-1', self.table_config)
        self.assertTrue(mock_update_scaling_policies.called)
        mock_update_scaling_policies.assert_called_with('test_table', 1, 5, 1, 5)

    @patch('dynamodb_scaling_controller.boto3.client')
    def test_update_scaling_policies_unsupported_region(self, mock_boto_client):
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        with self.assertRaises(ValueError):
            self.scaler.update_scaling_policies('unsupported-region', 'test_table', 1, 5, 1, 5)

    def test_main_scale_out(self):
        with patch('dynamodb_scaling_controller.config', Mock(scale='out')), \
             patch.object(dynamodb_scaling_controller.DynamoDBScaler, 'scale_out_dynamodb') as mock_scale_out:
            dynamodb_scaling_controller.main()
            mock_scale_out.assert_called_once()

    def test_main_scale_in(self):
        with patch('dynamodb_scaling_controller.config', Mock(scale='in')), \
             patch.object(dynamodb_scaling_controller.DynamoDBScaler, 'scale_in_dynamodb') as mock_scale_in:
            dynamodb_scaling_controller.main()
            mock_scale_in.assert_called_once()

if __name__ == '__main__':
    unittest.main()