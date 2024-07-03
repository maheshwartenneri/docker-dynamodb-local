import sys
import io
import os
from unittest.mock import patch, Mock
import unittest
import pytest

# Assuming dynamic_scaling_controller is in the "lambda_python" directory
path = os.path.abspath("lambda_python")
sys.path.append(path)
print(sys.path)

import dynamic_scaling_controller

class TestScript(unittest.TestCase):
    def setUp(self):
        pass

    def test_lambda_handler(self):
        self.assertEqual(dynamic_scaling_controller.lambda_handler(None, None), {
            "body": {"status": "Failure"},
            "statusCode": 400,
        })

    class DummyConfig:
        def __init__(self, event):
            if 'Records' in event:
                self.message = event['Records'][0]['Sns']['Message'].replace('\'', '')
                self.profile = self.message['profile'].strip().lower()
                self.scale = self.message['scale'].strip().lower()
            elif ('profile' and 'scale') in event:
                self.profile = event['profile'].strip().lower()
                self.scale = event['scale'].strip().lower()

        def read_from_s3(self, bucket, path):
            print("reading from S3")

    def test_autoscaling_group_waiter(self):
        self.assertEqual(dynamic_scaling_controller.autoscaling_group_waiter(None, None, 3, 2, 1), {
            "body": {"status": "Failure"},
            "statusCode": 400,
        })

    class DummyAwsClient:
        def instances_in_service(self, region_name, autoscaling_group_name):
            return 1

    def test_autoscaling_group_waiter_with_exception(self):
        dynamic_scaling_controller.aws_client = self.DummyAwsClient()
        with pytest.raises(RuntimeError) as error:
            dynamic_scaling_controller.autoscaling_group_waiter('us-east-1', 'dev-ecs-fargate', 10, 0.01, 1)
        self.assertIn("Timed out waiting for asg: dev-ecs-fargate-us-east-1-asg to scale to 10", str(error.value))

    class DummyConfigForScaling:
        def __init__(self):
            self.cluster_scaling_configs = [
                {
                    "cluster_name_pattern": "*pfc-dev-test.*",
                    "asg_scale_out": 3,
                    "asg_scale_in": 1,
                    "task_scale_configs": [
                        {
                            "name": "partic",
                            "scale_out_count": 4,
                            "scale_in_count": 1
                        }
                    ],
                    "dynamodb": {
                        "table_name": "dummy_table",
                        "scale_out_min_read_capacity": 5,
                        "scale_out_max_read_capacity": 10,
                        "scale_out_min_write_capacity": 5,
                        "scale_out_max_write_capacity": 10,
                        "scale_in_min_read_capacity": 1,
                        "scale_in_max_read_capacity": 5,
                        "scale_in_min_write_capacity": 1,
                        "scale_in_max_write_capacity": 5
                    }
                }
            ]

    class DummyAwsClientForScaling:
        def list_clusters(self, region_name, cluster_name_pattern):
            return ['pfc-dev-test']

        def scale_asg_count(self, asg_count, region_name, cluster):
            print("Scaling ASG")

        def update_scaling_policies(self, region_name, table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity):
            print(f"Scaling DynamoDB table {table_name} in {region_name}")

    def test_scale_out_all_asg_count(self):
        dynamic_scaling_controller.aws_client = self.DummyAwsClientForScaling()
        self.assertIsNone(dynamic_scaling_controller.scale_out_all_asg_count('us-east-1', self.DummyConfigForScaling()))

    def test_scale_in_all_asg_count(self):
        dynamic_scaling_controller.aws_client = self.DummyAwsClientForScaling()
        self.assertIsNone(dynamic_scaling_controller.scale_in_all_asg_count('us-east-1', self.DummyConfigForScaling()))

    class DummyAwsClientForServices:
        def scale_task_count(self, task_count, cluster_name, service_name, region_name):
            print("Scaling task count")

    def test_scale_in_services(self):
        dynamic_scaling_controller.aws_client = self.DummyAwsClientForServices()
        self.assertIsNone(dynamic_scaling_controller.scale_in_services('us-east-1', 'dev-ecs-fargate', [
            {
                "name": "partic",
                "scale_out_count": 4,
                "scale_in_count": 1
            }
        ], ['partic', 'collat', 'ledger']))

    def test_scale_out_services(self):
        dynamic_scaling_controller.aws_client = self.DummyAwsClientForServices()
        self.assertIsNone(dynamic_scaling_controller.scale_out_services('us-east-1', 'dev-ecs-fargate', [
            {
                "name": "partic",
                "scale_out_count": 4,
                "scale_in_count": 1
            }
        ], ['partic', 'collat', 'ledger']))

    def test_scale_out_all_services(self):
        dynamic_scaling_controller.aws_client = self.DummyAwsClientForScaling()
        self.assertIsNone(dynamic_scaling_controller.scale_out_all_services('us-east-1', self.DummyConfigForScaling()))

    def test_scale_in_all_services(self):
        dynamic_scaling_controller.aws_client = self.DummyAwsClientForScaling()
        self.assertIsNone(dynamic_scaling_controller.scale_in_all_services('us-east-1', self.DummyConfigForScaling()))

    def test_scale_out_dynamodb(self):
        dynamic_scaling_controller.aws_client = self.DummyAwsClientForScaling()
        config = self.DummyConfigForScaling().cluster_scaling_configs[0]['dynamodb']
        self.assertIsNone(dynamic_scaling_controller.scale_out_dynamodb('us-east-1', config))

    def test_scale_in_dynamodb(self):
        dynamic_scaling_controller.aws_client = self.DummyAwsClientForScaling()
        config = self.DummyConfigForScaling().cluster_scaling_configs[0]['dynamodb']
        self.assertIsNone(dynamic_scaling_controller.scale_in_dynamodb('us-east-1', config))

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
