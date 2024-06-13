import os
import json

def lambda_handler(event, context):  # pragma: no cover
    if not event:
        return {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }

    config = Config(event)
    environment = os.getenv("ENV", "dev").strip()
    bucket = os.getenv("BUCKET_NAME", "dynamic-scaling-lambda-dev-us-east-1").strip()
    path = f'profiles/{environment}/{config.profile}'
    config.read_from_s3(bucket, path)

    # Load the environment.json file
    with open('environment.json', 'r') as f:
        env_config = json.load(f)

    if config.scale == "out":
        print("Scaling out ASGs...")
        scale_out_all_asg_count('us-east-1', config=config)
        scale_out_all_asg_count('us-west-2', config=config)
        print("ASG scale out complete. \n")

        print("Scaling out services...")
        scale_out_all_services('us-east-1', config=config)
        scale_out_all_services('us-west-2', config=config)
        print("Service scale out complete.")
        
        # DynamoDB scaling example call
        aws_client = AWSClient()
        aws_client.creation_table_scaling(env_config)
        print("DynamoDB scaling complete.")
        
    elif config.scale == "in":
        print("Scaling in services...")
        scale_in_all_services('us-east-1', config=config)
        scale_in_all_services('us-west-2', config=config)
        print("Service scale in complete. \n")
        
        print("Scaling in ASGs...")
        scale_in_all_asg_count('us-east-1', config=config)
        scale_in_all_asg_count('us-west-2', config=config)
        print("ASG scale in complete")
    else:
        raise ValueError(f'Invalid parameter, event: {event}')