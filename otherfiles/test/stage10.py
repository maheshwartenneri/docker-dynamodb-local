import unittest
import sys
import io
import os
from unittest.mock import patch, Mock
from lib import aws_client
import pytest

path = os.path.abspath("lambda_python")
sys.path.append(path)
print(sys.path)
import dynamic_scaling_controller

class TestScript(unittest.TestCase): # pragma: no cover

    def setUp(self):
        pass

    def test_lambda_handler(self):
        assert dynamic_scaling_controller.lambda_handler(None, None) == {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }

    class DummyConfig:
        def __init__(self, event):
            if 'Records' in event:
                self.message = event['Records'][0]['Sns']['Message'].replace('\\', '')
                self.profile = self.message['profile'].strip().lower()
                self.scale = self.message['scale'].strip().lower()
            elif ('profile' and 'scale') in event:
                self.profile = event['profile'].strip().lower()
                self.scale = event['scale'].strip().lower()

        def read_from_s3(self, bucket, path):
            print("reading from S3")

    event = {
        "scale": "out",
        "profile": "triggeredbysns.json"
    }

    def test_autoscaling_group_waiter(self):
        assert dynamic_scaling_controller.autoscaling_group_waiter(None, None, 3, 2, 1) == {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }

    class DummyAwsClient:
        def instances_in_service(self, self, region_name, autoscaling_group_name):
            return 1

    dynamic_scaling_controller.aws_client = DummyAwsClient()

    def test_scale_out_all_asg_count(self):
        assert dynamic_scaling_controller.scale_out_all_asg_count('us-east-1', DummyConfig()) is None

    def test_scale_in_all_asg_count(self):
        assert dynamic_scaling_controller.scale_in_all_asg_count(None, None, None) == {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }

    class DummyConfig:
        def __init__(self):
            self.cluster_scaling_configs = [
                {
                    "cluster_name_pattern": ".*pfc-dev-test.*",
                    "asg_scale_out": 3,
                    "asg_scale_in": 1,
                    "task_scale_configs": [
                        {
                            "name": "partic",
                            "scale_out_count": 4,
                            "scale_in_count": 1,
                        }
                    ]
                }
            ]

    class DummyAwsClient:
        def list_clusters(self, self, region_name, cluster_name_pattern):
            return ['pfc-dev-test']

        def scale_asg_count(self, self, asg_count, region_name, cluster):
            print("Scaling ASG")

        def ecs_service_waiter(self, region_name, cluster_name, services_to_poll, poll_interval=10, max_polls=15):
            print("Check status of ecs services")

        def scale_task_count(self, task_count, cluster_name, service_name, region_name):
            print("Scaling task count")

        def list_clusters(self, region_name, cluster_name_pattern):
            return ['pfc-test-dev']

        def list_all_ecs_services(self, region_name, cluster_name):
            return ['collat', 'attrib']

    dynamic_scaling_controller.aws_client = DummyAwsClient()

    def test_scale_in_services(self):
        assert dynamic_scaling_controller.scale_in_services(None, None, None, None) == {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }

    def test_scale_out_all_services(self):
        assert dynamic_scaling_controller.scale_out_all_services(None, None) == {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }

    def tearDown(self):
        pass

# Adding DynamoDB test cases

class TestDynamoDB(unittest.TestCase): # pragma: no cover

    def test_update_scaling_policies(self):
        assert dynamic_scaling_controller.update_scaling_policies('us-east-1', 'test-table', 1, 10, 1, 10) is None

    class DummyAwsClient:
        def register_scalable_target(self, ServiceNamespace, ResourceId, ScalableDimension, MinCapacity, MaxCapacity):
            print(f"Updating scalable target for {ResourceId} with {MinCapacity} - {MaxCapacity}")

    dynamic_scaling_controller.aws_client = DummyAwsClient()

    class DummyConfig:
        def __init__(self):
            self.dynamodb_scaling_configs = [
                {
                    "table_name": "test-table",
                    "scale_out_min_read_capacity": 1,
                    "scale_out_max_read_capacity": 10,
                    "scale_out_min_write_capacity": 1,
                    "scale_out_max_write_capacity": 10,
                    "scale_in_min_read_capacity": 1,
                    "scale_in_max_read_capacity": 10,
                    "scale_in_min_write_capacity": 1,
                    "scale_in_max_write_capacity": 10,
                }
            ]

    def test_scale_out_dynamodb(self):
        config = self.DummyConfig()
        for table_config in config.dynamodb_scaling_configs:
            assert dynamic_scaling_controller.scale_out_dynamodb('us-east-1', table_config) is None

    def test_scale_in_dynamodb(self):
        config = self.DummyConfig()
        for table_config in config.dynamodb_scaling_configs:
            assert dynamic_scaling_controller.scale_in_dynamodb('us-east-1', table_config) is None

if __name__ == '__main__':
    unittest.main()