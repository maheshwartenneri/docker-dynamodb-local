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
        instances_in_service_count = aws_client.instances_in_service(region_name, autoscaling_group_name)
        print(f'Instances in service: {instances_in_service_count}')
        print(f'Desired capacity: {asg_desired_capacity}')
        time.sleep(polling_interval)

    if instances_in_service_count != asg_desired_capacity:
        raise RuntimeError(f'Timed out waiting for ASG: {autoscaling_group_name} to scale to {asg_desired_capacity}')

def scale_asg_count(region_name, config, scale_type):
    if not region_name or not config:
        return {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }

    scaled_configs = []
    for cluster_config in config.cluster_scaling_configs:
        scale_count_key = f'asg_scale_{scale_type}'
        if scale_count_key not in cluster_config:
            continue
        cluster_list = aws_client.list_clusters(region_name, cluster_config['cluster_name_pattern'])
        scaled_configs += [{'cluster': cluster, scale_count_key: cluster_config[scale_count_key]} for cluster in cluster_list]

    for cluster in cluster_list:
        aws_client.scale_asg_count(cluster_config[scale_count_key], region_name, cluster)
    
    print(f'Waiting for instances to reach a stable state in region: {region_name}')
    for config in scaled_configs:
        autoscaling_group_waiter(region_name, config['cluster'], config[scale_count_key])
    print(f'Instances are stable in region: {region_name}')

def scale_services(region_name, config, scale_type):
    if not region_name or not config:
        return {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }

    scaled_services_config = []
    for cluster_config in config.cluster_scaling_configs:
        for cluster in aws_client.list_clusters(region_name, cluster_config['cluster_name_pattern']):
            service_list = aws_client.list_all_ecs_services(cluster, region_name)
            task_scale_configs = cluster_config['task_scale_configs']
            for task_config in task_scale_configs:
                scale_count_key = f'scale_{scale_type}_count'
                if scale_count_key not in task_config:
                    continue
                if not any(re.match(task_config['service_name_pattern'], service) for service in service_list):
                    continue
                scaled_services_config += [{
                    'cluster': cluster,
                    'service': service,
                    'scale_count': task_config[scale_count_key]
                } for service in service_list if re.match(task_config['service_name_pattern'], service)]

    print(f'Waiting for services to reach a stable state in region: {region_name}')
    for config in scaled_services_config:
        aws_client.scale_task_count(config['scale_count'], config['cluster'], config['service'], region_name)
        aws_client.ecs_service_waiter(region_name, config['cluster'], [config['service']])
    print(f'Services are stable in region: {region_name}')

# DynamoDB Scaling Functions
def scale_dynamodb(region_name, dynamodb_scaling_configs, scale_type):
    if not dynamodb_scaling_configs:
        return

    application_autoscaling_client = boto3.client('application-autoscaling', region_name=region_name)
    table_name_pattern_key = 'table_name_pattern'
    read_capacity_key = f'read_capacity_{scale_type}'
    write_capacity_key = f'write_capacity_{scale_type}'

    for config in dynamodb_scaling_configs:
        if table_name_pattern_key not in config or read_capacity_key not in config or write_capacity_key not in config:
            continue

        dynamodb_client = boto3.client('dynamodb', region_name=region_name)
        paginator = dynamodb_client.get_paginator('list_tables')
        table_names = []
        for page in paginator.paginate():
            table_names.extend(page['TableNames'])

        matching_tables = [table_name for table_name in table_names if re.match(config[table_name_pattern_key], table_name)]
        for table_name in matching_tables:
            application_autoscaling_client.register_scalable_target(
                ServiceNamespace='dynamodb',
                ResourceId=f'table/{table_name}',
                ScalableDimension='dynamodb:table:ReadCapacityUnits',
                MinCapacity=config[read_capacity_key],
                MaxCapacity=config[read_capacity_key]
            )
            application_autoscaling_client.register_scalable_target(
                ServiceNamespace='dynamodb',
                ResourceId=f'table/{table_name}',
                ScalableDimension='dynamodb:table:WriteCapacityUnits',
                MinCapacity=config[write_capacity_key],
                MaxCapacity=config[write_capacity_key]
            )

def scale(region_name, config, scale_type):
    if not region_name or not config:
        return {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }
    
    scale_asg_count(region_name, config, scale_type)
    scale_services(region_name, config, scale_type)
    scale_dynamodb(region_name, config.dynamodb_scaling_configs, scale_type)

def lambda_handler(event, context):  # pragma: no cover
    try:
        print(f'Received event: {event}')
        config = Config(event)
        scale_type = config.scale

        scale('us-east-1', config, scale_type)
        scale('us-west-2', config, scale_type)

        response = {
            "body": {"status": "Success"},
            "statusCode": 200,
        }
    except Exception as e:
        print(f'Failed to process event {event} with error: {e}')
        response = {
            "body": {"status": "Failure", "error": str(e)},
            "statusCode": 500,
        }
    
    return response
