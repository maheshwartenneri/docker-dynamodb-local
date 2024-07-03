import boto3
import re
import json
import time
import os

s3 = boto3.resource('s3')

# AWS Client
class AWSClient:  # pragma: no cover
    def __init__(self):
        self.east_autoscaling = boto3.client('autoscaling', region_name='us-east-1')
        self.west_autoscaling = boto3.client('autoscaling', region_name='us-west-2')
        self.east_application_autoscaling = boto3.client('application-autoscaling', region_name='us-east-1')
        self.west_application_autoscaling = boto3.client('application-autoscaling', region_name='us-west-2')
        self.east_ecs = boto3.client('ecs', region_name='us-east-1')
        self.west_ecs = boto3.client('ecs', region_name='us-west-2')
        self.east_dynamodb = boto3.client('application-autoscaling', region_name='us-east-1')
        self.west_dynamodb = boto3.client('application-autoscaling', region_name='us-west-2')

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

    def update_scaling_policies(self, region_name, table_name, min_read_capacity, max_read_capacity, min_write_capacity, max_write_capacity):
        if region_name == 'us-east-1':
            aws_region_client = self.east_dynamodb
        elif region_name == 'us-west-2':
            aws_region_client = self.west_dynamodb
        else:
            raise ValueError(f'Unsupported region: {region_name}')
        
        try:
            # Update scalable target for read capacity
            aws_region_client.register_scalable_target(
                ServiceNamespace='dynamodb',
                ResourceId=f'table/{table_name}',
                ScalableDimension='dynamodb:table:ReadCapacityUnits',
                MinCapacity=min_read_capacity,
                MaxCapacity=max_read_capacity
            )
            # Update scalable target for write capacity
            aws_region_client.register_scalable_target(
                ServiceNamespace='dynamodb',
                ResourceId=f'table/{table_name}',
                ScalableDimension='dynamodb:table:WriteCapacityUnits',
                MinCapacity=min_write_capacity,
                MaxCapacity=max_write_capacity
            )
            print(f"Auto-scaling settings for '{table_name}' updated successfully.")
            print(f"Read Capacity Range: {min_read_capacity} - {max_read_capacity}")
            print(f"Write Capacity Range: {min_write_capacity} - {max_write_capacity}")
        except Exception as e:
            print(f"Error updating auto-scaling settings for '{table_name}': {e}")

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
        raise TimeoutError(f'Timed out waiting for {asg_desired_capacity} instances in ASG ({autoscaling_group_name}) to be InService.')

# ECS Service Waiter
def ecs_service_waiter(region_name, cluster_name, services_to_poll, poll_interval=10, max_polls=15):
    if not region_name or not cluster_name:
        return {
            "body": {"status": "Failure"},
            "statusCode": 400,
        }
    
    aws_client.ecs_service_waiter(region_name, cluster_name, services_to_poll, poll_interval, max_polls)

def lambda_handler(event, context):
    config = Config(event)
    config.read_from_s3(
        os.environ['Scaling_Config_Bucket'],
        os.environ['Scaling_Config_Path']
    )
    
    cluster_scaling_config = config.cluster_scaling_configs[config.profile]

    for region_name in ['us-east-1', 'us-west-2']:
        cluster_list = aws_client.list_clusters(region_name, cluster_scaling_config['ecs_cluster_name_pattern'])
        print(f'Found {len(cluster_list)} clusters in {region_name} matching pattern: {cluster_scaling_config["ecs_cluster_name_pattern"]}')

        for cluster_name in cluster_list:
            if config.scale == 'up':
                aws_client.scale_asg_count(cluster_scaling_config['asg_desired_capacity'], region_name, cluster_name)
                autoscaling_group_waiter(region_name, cluster_name, cluster_scaling_config['asg_desired_capacity'])
                service_list = aws_client.list_all_ecs_services(cluster_name, region_name)
                for service_name in service_list:
                    aws_client.scale_task_count(cluster_scaling_config['task_desired_count'], cluster_name, service_name, region_name)
                ecs_service_waiter(region_name, cluster_name, service_list)

                # Update DynamoDB scaling policies
                aws_client.update_scaling_policies(
                    region_name,
                    cluster_scaling_config['dynamodb_table_name'],
                    cluster_scaling_config['dynamodb_min_read_capacity'],
                    cluster_scaling_config['dynamodb_max_read_capacity'],
                    cluster_scaling_config['dynamodb_min_write_capacity'],
                    cluster_scaling_config['dynamodb_max_write_capacity']
                )

            elif config.scale == 'down':
                service_list = aws_client.list_all_ecs_services(cluster_name, region_name)
                for service_name in service_list:
                    aws_client.scale_task_count(0, cluster_name, service_name, region_name)
                ecs_service_waiter(region_name, cluster_name, service_list)
                aws_client.scale_asg_count(0, region_name, cluster_name)
                autoscaling_group_waiter(region_name, cluster_name, 0)

                # Update DynamoDB scaling policies
                aws_client.update_scaling_policies(
                    region_name,
                    cluster_scaling_config['dynamodb_table_name'],
                    0, 0, 0, 0
                )

aws_client = AWSClient()
