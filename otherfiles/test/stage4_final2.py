from lambda_python import dynamic_scaling_controller
import unittest
import sys
import os
from unittest.mock import patch, Mock
import pytest

path = os.path.abspath("lambda_python")
sys.path.append(path)
print(sys.path)
import dynamic_scaling_controller

class TestScript(unittest.TestCase):  # pragma: no cover
    def setUp(self):
        # self.event={"profile":"envprof.dev.json", "scale":"up"}
        # config = dynamic_scaling_controller.Config(self.event)
        pass

    def test_lambda_handler(self):
        assert dynamic_scaling_controller.lambda_handler(None, None) == {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }

    def test_autoscaling_group_waiter(self):
        assert dynamic_scaling_controller.autoscaling_group_waiter(None, None, 3, 2, 1) == {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }

    def test_scale_out_all_asg_count(self):
        assert dynamic_scaling_controller.scale_out_all_asg_count(None, None) == {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }

    def test_scale_in_all_asg_count(self):
        assert dynamic_scaling_controller.scale_in_all_asg_count(None, None) == {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }

    def test_scale_out_dynamodb(self):
        dynamic_scaling_controller.aws_client = DummyAwsClient()
        config = DummyConfig().cluster_scaling_configs[0]['dynamodb']
        assert dynamic_scaling_controller.scale_out_dynamodb('us-east-1', config) is None

    def test_scale_in_dynamodb(self):
        dynamic_scaling_controller.aws_client = DummyAwsClient()
        config = DummyConfig().cluster_scaling_configs[0]['dynamodb']
        assert dynamic_scaling_controller.scale_in_dynamodb('us-east-1', config) is None

class DummyConfig:
    def __init__(self, event=None):
        if event and 'Records' in event:
            self.message = event['Records'][0]['Sns']['Message'].replace('\\', "")
            self.profile = self.message['profile'].strip().lower()
            self.scale = self.message['scale'].strip().lower()
        elif event and ('profile' and 'scale') in event:
            self.profile = event['profile'].strip().lower()
            self.scale = event['scale'].strip().lower()
        else:
            self.cluster_scaling_configs = [
                {
                    "cluster_name_pattern": ".*pfc-dev-test.*",
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

    def read_from_s3(self, bucket, path):
        print("reading from S3")

event = {
    "scale": "out",
    "profile": "triggeredbysns.json"
}

class DummyAwsClient:
    def ecs_service_waiter(self, region_name, cluster_name, services_to_poll, poll_interval=10, max_polls=15):
        print("Check status of ecs services")

    def scale_task_count(self, task_count, cluster_name, service_name, region_name):
        print("Scaling task count")

    def list_clusters(self, region_name, cluster_name_pattern):
        return ['pfc-dev-test']

    def list_all_ecs_services(self, region_name, cluster_name):
        return ['partic', 'collat', 'ledger']

    def scale_asg_count(self, asg_count, region_name, cluster):
        print("Scaling ASG")

    def instances_in_service(self, region_name, autoscaling_group_name):
        return 1

    def scale_in_services(self, region_name, task_scale_configs, service_list):
        print("scale in all services")

    def scale_out_services(self, region_name, task_scale_configs, service_list):
        print("scale out all services")

    def update_scaling_policies(self, region_name, table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity):
        print(f"Scaling DynamoDB table {table_name} in {region_name}")

dynamic_scaling_controller.aws_client = DummyAwsClient()

with pytest.raises(RuntimeError) as error:
    dynamic_scaling_controller.autoscaling_group_waiter('us-east-1', 'dev-ecs-fargate', 10, 0.01, 1)
assert "Timeout waiting for asg: dev-ecs-fargate-us-east-1-asg to scale to 10" in str(error.value)

assert dynamic_scaling_controller.scale_out_all_asg_count('us-east-1', DummyConfig()) is None
assert dynamic_scaling_controller.scale_in_all_asg_count('us-east-1', DummyConfig()) is None

if __name__ == '__main__':
    unittest.main()