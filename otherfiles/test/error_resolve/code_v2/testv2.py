Here is the test case code adapted from the images to match the updated function you provided earlier:

```python
import unittest
from unittest.mock import patch, Mock
import os
import sys

# Append the path for the dynamic_scaling_controller module
path = os.path.abspath("lambda_python")
sys.path.append(path)
print(sys.path)

import dynamic_scaling_controller

class TestScript(unittest.TestCase):
    def setUp(self):
        # Setup mock event and configuration
        self.event = {
            "profile": "envprof.dev.json",
            "scale": "up"
        }
        # Config = dynamic_scaling_controller.Config(self.event)
        pass

    def test_lambda_handler(self):
        # Test lambda handler
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
            print("Reading from S3")
        
        cluster_scaling_configs = {
            "tables": {
                "table_name": "test-table",
                "scale_out_min_read_capacity": 1,
                "scale_out_max_read_capacity": 10,
                "scale_out_min_write_capacity": 1,
                "scale_out_max_write_capacity": 10
            }
        }

    def test_scale_out_dynamodb(self):
        # Test scale out dynamodb
        dynamic_scaling_controller.aws_client = self.DummyAwsClient()
        assert dynamic_scaling_controller.scale_out_dynamodb('us-east-1', self.DummyConfig(self.event)) is None

    class DummyAwsClient:
        def update_scaling_policies(self, aws_region_client, table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity):
            print("Updating scalable target for dynamodb")
        
    def test_scale_in_dynamodb(self):
        # Test scale in dynamodb
        dynamic_scaling_controller.aws_client = self.DummyAwsClient()
        assert dynamic_scaling_controller.scale_in_dynamodb('us-east-1', self.DummyConfig(self.event)) is None

    def tearDown(self):
        pass

if __name__ == "__main__":
    unittest.main()
```

### Explanation:
- The `DummyConfig` class is used to mock the configuration read from S3.
- The `DummyAwsClient` class is used to mock the AWS client methods.
- The test methods (`test_scale_out_dynamodb` and `test_scale_in_dynamodb`) are set up to test the scaling functions.
- `unittest.main()` is called to run the tests.

Make sure to adjust the import paths and configuration details as necessary to match your specific environment and setup.