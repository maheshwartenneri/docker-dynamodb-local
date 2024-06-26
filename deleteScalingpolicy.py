import boto3

class DynamoDBScaler:
    def __init__(self):
        self.scaling_dynamodb = boto3.client('application-autoscaling')

    def delete_existing_policies(self, table_name):
        response = self.scaling_dynamodb.describe_scaling_policies(
            ServiceNamespace='dynamodb',
            ResourceId=f'table/{table_name}'
        )
        policies = response.get('ScalingPolicies', [])

        if not policies:
            print(f"No scaling policies found for table '{table_name}'.")
            return

        for policy in policies:
            self.scaling_dynamodb.delete_scaling_policy(
                ServiceNamespace='dynamodb',
                ResourceId=f'table/{table_name}',
                PolicyName=policy['PolicyName'],
                ScalableDimension=policy['ScalableDimension']
            )
            print(f"Deleted scaling policy: {policy['PolicyName']}")

if __name__ == '__main__':
    table_name = 'dev-lgr-inst'
    scaler = DynamoDBScaler()
    scaler.delete_existing_policies(table_name)