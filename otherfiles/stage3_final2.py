import boto3
import re
import json
import time
import os

# AWS Client
class AWSClient:  # pragma: no cover
    def __init__(self):
        self.east_autoscaling = boto3.client('autoscaling', region_name='us-east-1')
        self.west_autoscaling = boto3.client('autoscaling', region_name='us-west-2')
        self.east_application_autoscaling = boto3.client('application-autoscaling', region_name='us-east-1')
        self.west_application_autoscaling = boto3.client('application-autoscaling', region_name='us-west-2')
        self.east_ecs = boto3.client('ecs', region_name='us-east-1')
        self.west_ecs = boto3.client('ecs', region_name='us-west-2')

    def instances_in_service(self, region_name, autoscaling_group_name):
        if region_name == 'us-east-1':
            aws_region_client = self.east_autoscaling
        elif region_name == 'us-west-2':
            aws_region_client = self.west_autoscaling
        else:
            raise ValueError(f'Unsupported region: {region_name}')
        
        response = aws_region_client.describe_auto_scaling_groups(
            AutoScalingGroupNames=[autoscaling_group_name]
        )
        
        if len(response['AutoScalingGroups']) != 1:
            raise ValueError(f'Parameter: {autoscaling_group_name} returned {len(response["AutoScalingGroups"])} ASGs. Expected a value of 1.')
        
        instances_list = response['AutoScalingGroups'][0]['Instances']
        return len([instance for instance in instances_list if instance['LifecycleState'] == 'InService'])

    def list_clusters(self, region_name, cluster_name_pattern):
        if region_name == 'us-east-1':
            aws_region_client = self.east_ecs
        elif region_name == 'us-west-2':
            aws_region_client = self.west_ecs
        else:
            raise ValueError(f'Unsupported region: {region_name}')
        
        try:
            response = aws_region_client.list_clusters()
            results = response['clusterArns']
            while "nextToken" in response:
                response = aws_region_client.list_clusters(nextToken=response["nextToken"])
                results.extend(response["clusterArns"])
            
            compiled_pattern = re.compile(cluster_name_pattern)
            cluster_list = [cluster_arn for cluster_arn in results if compiled_pattern.match(cluster_arn)]
            return [cluster_arn.split('/')[1] for cluster_arn in cluster_list]
        
        except aws_region_client.exceptions.ServerException as error:
            raise RuntimeError(f'Region: {region_name}. Failed to list clusters due to server error: {error}')
        
        except aws_region_client.exceptions.ClientException as error:
            raise RuntimeError(f'Region: {region_name}. Failed to list clusters due to client error: {error}')

    def scale_asg_count(self, asg_count, region_name, cluster):
        if region_name == 'us-east-1':
            aws_region_client = self.east_autoscaling
        elif region_name == 'us-west-2':
            aws_region_client = self.west_autoscaling
        else:
            raise ValueError(f'Unsupported region: {region_name}')
        
        try:
            print(f'{cluster}-{region_name}-asg')
            response = aws_region_client.update_auto_scaling_group(
                AutoScalingGroupName=f'{cluster}-{region_name}-asg',
                MinSize=asg_count,
                MaxSize=asg_count,
                DesiredCapacity=asg_count
            )
        except aws_region_client.exceptions.ScalingActivityInProgressFault as error:
            raise RuntimeError(f'Failed to scale ASG: {cluster}-{region_name}-asg. Another scaling action is in progress: {error}')

    def ecs_service_waiter(self, region_name, cluster_name, services_to_poll, poll_interval=10, max_polls=15):
        if region_name == 'us-east-1':
            aws_region_client = self.east_ecs
        elif region_name == 'us-west-2':
            aws_region_client = self.west_ecs
        else:
            raise ValueError(f'Unsupported region: {region_name}')

        waiter = aws_region_client.get_waiter("services_stable")
        response = waiter.wait(
            cluster=cluster_name,
            services=services_to_poll,
            WaiterConfig={"Delay": poll_interval, "MaxAttempts": max_polls}
        )
        return response

    def scale_task_count(self, task_count, cluster_name, service_name, region_name):
        if region_name == 'us-east-1':
            aws_region_client = self.east_application_autoscaling
        elif region_name == 'us-west-2':
            aws_region_client = self.west_application_autoscaling
        else:
            raise ValueError(f'Unsupported region: {region_name}')

        response = aws_region_client.register_scalable_target(
            ServiceNamespace='ecs',
            ResourceId=f'service/{cluster_name}/{service_name}',
            ScalableDimension='ecs:service:DesiredCount',
            MinCapacity=task_count,
            MaxCapacity=task_count
        )
        return response

    def list_all_ecs_services(self, cluster_name, region_name):
        if region_name == 'us-east-1':
            aws_region_client = self.east_ecs
        elif region_name == 'us-west-2':
            aws_region_client = self.west_ecs
        else:
            raise ValueError(f'Unsupported region: {region_name}')

        response = aws_region_client.list_services(cluster=cluster_name)
        return [service.split('/')[2] for service in response['serviceArns']]

    def register_dynamodb_scaling_policy(self, table_name, region_name, read_capacity, write_capacity):
        if region_name == 'us-east-1':
            application_autoscaling_client = self.east_application_autoscaling
        elif region_name == 'us-west-2':
            application_autoscaling_client = self.west_application_autoscaling
        else:
            raise ValueError(f'Unsupported region: {region_name}')

        application_autoscaling_client.register_scalable_target(
            ServiceNamespace='dynamodb',
            ResourceId=f'table/{table_name}',
            ScalableDimension='dynamodb:table:ReadCapacityUnits',
            MinCapacity=read_capacity,
            MaxCapacity=read_capacity
        )
        application_autoscaling_client.register_scalable_target(
            ServiceNamespace='dynamodb',
            ResourceId=f'table/{table_name}',
            ScalableDimension='dynamodb:table:WriteCapacityUnits',
            MinCapacity=write_capacity,
            MaxCapacity=write_capacity
        )

aws_client = AWSClient()

# Config
class Config:  # pragma: no cover
    def __init__(self, event):
        if 'Records' in event:
            self.message = json.loads(event['Records'][0]['Sns']['Message']).replace('*', '***')
            self.profile = self.message['profile'].strip().lower()
            self.scale = self.message['scale'].strip().lower()
        elif 'profile' in event and 'scale' in event:
            self.profile = event['profile'].strip().lower()
            self.scale = event['scale'].strip().lower()

    def read_from_s3(self, bucket, path):
        content_object = s3.Object(bucket, path)
        file_content = content_object.get()['Body'].read().decode('utf-8')
        self.cluster_scaling_configs = json.loads(file_content)
        self.dynamodb_scaling_configs = self.cluster_scaling_configs.get('dynamodb', [])

# ASG and ECS Waiters
# Autoscaling Group Waiter
def autoscaling_group_waiter(region_name, cluster_name, asg_desired_capacity, polling_interval=10, max_polls=15):
    if not region_name or not cluster_name:
        return {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }
    
    autoscaling_group_name = f'{cluster_name}-{region_name}-asg'
    instances_in_service_count = 0
    poll_counter = 0

    while instances_in_service_count != asg_desired_capacity and poll_counter < max_polls:
        poll_counter += 1
        # Continuously poll the ASG for the instances' lifecycle state
        instances_in_service_count = aws_client.instances_in_service(region_name, autoscaling_group_name)
        print(f'Instances in service: {instances_in_service_count}')
        print(f'Desired capacity: {asg_desired_capacity}')
        time.sleep(polling_interval)

    if instances_in_service_count != asg_desired_capacity:
        raise RuntimeError(f'Timed out waiting for ASG: {autoscaling_group_name} to scale to {asg_desired_capacity}')

# Scales ASG Size
def scale_out_all_asg_count(region_name, config):
    if not region_name or not config:
        return {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }

    scaled_configs = []
    for cluster_config in config.cluster_scaling_configs:
        if "asg_scale_out" not in cluster_config:
            continue
        cluster_list = aws_client.list_clusters(region_name, cluster_config['cluster_name_pattern'])
        scaled_configs += [{'cluster': cluster, 'asg_scale_out': cluster_config['asg_scale_out']} for cluster in cluster_list]

    for cluster in cluster_list:
        aws_client.scale_asg_count(cluster_config['asg_scale_out'], region_name, cluster)
    
    print(f'Waiting for instances to reach a stable state in region: {region_name}')
    try:
        for config in scaled_configs:
            autoscaling_group_waiter(region_name, config['cluster'], config['asg_scale_out'])
        print(f'Instances are stable in region: {region_name}')
    except:
        print("Instances are unstable.")

def scale_in_all_asg_count(region_name, config):
    if not region_name or not config:
        return {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }

    scaled_configs = []
    for cluster_config in config.cluster_scaling_configs:
        if "asg_scale_in" not in cluster_config:
            continue
        cluster_list = aws_client.list_clusters(region_name, cluster_config['cluster_name_pattern'])
        scaled_configs += [{'cluster': cluster, 'asg_scale_in': cluster_config['asg_scale_in']} for cluster in cluster_list]

    for cluster in cluster_list:
        aws_client.scale_asg_count(cluster_config['asg_scale_in'], region_name, cluster)

    print(f'Waiting for instances to reach a stable state in region: {region_name}')
    for config in scaled_configs:
        autoscaling_group_waiter(region_name, config['cluster'], config['asg_scale_in'])
    print(f'Instances are stable in region: {region_name}')

def scale_in_services(region_name, cluster_name, task_scale_configs, service_list):
    if not region_name or not cluster_name or not task_scale_configs or not service_list:
        return {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }
    # Update the task count of the service if the "task" name is in the service list
    for task_config in task_scale_configs:
        for service in service_list:
            if task_config['name'] in service:
                aws_client.scale_task_count(task_config['scale_in_count'], cluster_name, service, region_name)
                break

def scale_out_services(region_name, cluster_name, task_scale_configs, service_list):
    if not region_name or not cluster_name or not task_scale_configs or not service_list:
        return {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }
    for task_config in task_scale_configs:
        for service in service_list:
            if task_config['name'] in service:
                aws_client.scale_task_count(task_config['scale_out_count'], cluster_name, service, region_name)
                break

def scale_out_all_services(region_name, config):
    if not region_name or not config:
        return {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }

    scaled_services_config = []
    for cluster_config in config.cluster_scaling_configs:
        for cluster in aws_client.list_clusters(region_name, cluster_config['cluster_name_pattern']):
            service_list = aws_client.list_all_ecs_services(cluster, region_name)
            scale_out_services(region_name, cluster, cluster_config['task_scale_configs'], service_list)
            scaled_services_config.append({'cluster': cluster, 'service_list': service_list})

    print(f'Waiting for services to reach a stable state in region: {region_name}')
    for config in scaled_services_config:
        if "fargate" in config['cluster'] or 'perf' in config['cluster']:
            continue
        aws_client.ecs_service_waiter(region_name, config['cluster'], config['service_list'])
    print(f'Services are stable in region: {region_name}')

def scale_in_all_services(region_name, config):
    if not region_name or not config:
        return {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }

    scaled_services_config = []
    for cluster_config in config.cluster_scaling_configs:
        for cluster in aws_client.list_clusters(region_name, cluster_config['cluster_name_pattern']):
            service_list = aws_client.list_all_ecs_services(cluster, region_name)
            scale_in_services(region_name, cluster, cluster_config['task_scale_configs'], service_list)
            scaled_services_config.append({'cluster': cluster, 'service_list': service_list})

    print(f'Waiting for services to reach a stable state in region: {region_name}')
    for config in scaled_services_config:
        if "fargate" in config['cluster'] or 'perf' in config['cluster']:
            continue
        aws_client.ecs_service_waiter(region_name, config['cluster'], config['service_list'])
    print(f'Services are stable in region: {region_name}')

def scale_dynamodb_tables(region_name, config):
    if not region_name or not config:
        return {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }

    for dynamodb_config in config.dynamodb_scaling_configs:
        table_name = dynamodb_config['table_name']
        read_capacity = dynamodb_config['read_capacity']
        write_capacity = dynamodb_config['write_capacity']
        aws_client.register_dynamodb_scaling_policy(table_name, region_name, read_capacity, write_capacity)

# Executed by the Lambda
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

    if config.scale == "out":
        print("Scaling out ASGs...")
        scale_out_all_asg_count('us-east-1', config=config)
        scale_out_all_asg_count('us-west-2', config=config)
        print("ASG scale out complete.\n")

        print("Scaling out services...")
        scale_out_all_services('us-east-1', config=config)
        scale_out_all_services('us-west-2', config=config)
        print("Service scale out complete.")

    elif config.scale == "in":
        print("Scaling in services...")
        scale_in_all_services('us-east-1', config=config)
        scale_in_all_services('us-west-2', config=config)
        print("Service scale in complete.\n")

        print("Scaling in ASGs...")
        scale_in_all_asg_count('us-east-1', config=config)
        scale_in_all_asg_count('us-west-2', config=config)
        print("ASG scale in complete")

    # New scaling action for DynamoDB tables
    print("Scaling DynamoDB tables...")
    scale_dynamodb_tables('us-east-1', config=config)
    scale_dynamodb_tables('us-west-2', config=config)
    print("DynamoDB table scaling complete.")

    else:
        raise ValueError(f'Invalid parameter, event: {event}')
