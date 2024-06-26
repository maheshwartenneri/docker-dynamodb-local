import boto3

class DynamoDBScaler:
    def __init__(self):
        self.scaling_dynamodb = boto3.client('application-autoscaling')

    def list_existing_policies(self, table_name):
        response = self.scaling_dynamodb.describe_scaling_policies(
            ServiceNamespace='dynamodb',
            ResourceId=f'table/{table_name}'
        )
        return response.get('ScalingPolicies', [])

if __name__ == '__main__':
    table_name = 'dev-lgr-inst'
    scaler = DynamoDBScaler()
    policies = scaler.list_existing_policies(table_name)

    if policies:
        print(f"Existing scaling policies for table '{table_name}':")
        for policy in policies:
            print(f"Policy Name: {policy['PolicyName']}")
            print(f"Scalable Dimension: {policy['ScalableDimension']}")
            print(f"Policy Type: {policy['PolicyType']}")
            print(f"Target Value: {policy['TargetTrackingScalingPolicyConfiguration']['TargetValue']}")
            print(f"Scale Out Cooldown: {policy['TargetTrackingScalingPolicyConfiguration']['ScaleOutCooldown']}")
            print(f"Scale In Cooldown: {policy['TargetTrackingScalingPolicyConfiguration']['ScaleInCooldown']}")
            print("-" * 50)
    else:
        print(f"No scaling policies found for table '{table_name}'.")