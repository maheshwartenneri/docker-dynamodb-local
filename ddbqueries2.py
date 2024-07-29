To convert the provided SQL queries into DynamoDB queries using Python (Boto3), we need to structure them based on DynamoDB's data model. Let's assume that the `contractId` is the partition key and `seqNum` or `transactionId` is the sort key.

### SQL Queries
1. **Get account state corresponding to a seqNum/transactionId**
    - SQL Query 1:
      ```sql
      SELECT contract_id, transaction_id, seq_num, ledger_state_hash, primary_event_hash
      FROM transaction_id
      WHERE contract_id = ? AND transaction_id = ?
      LIMIT 1;
      ```
    - SQL Query 2:
      ```sql
      SELECT contract_id, seq_num, transaction_id, prev_transaction_id, instrument_class_id, lamport_timestamp, start_instrument_id, end_instrument_id, state_hash, primary_event_hash, account_mode, maintenance_lifecycle_account_state, state, crypto_digest
      FROM state
      WHERE contract_id = ? AND seq_num = ?
      LIMIT 1;
      ```

2. **Get current account state**
    - SQL Query:
      ```sql
      SELECT contract_id, seq_num, transaction_id, prev_transaction_id, instrument_class_id, lamport_timestamp, start_instrument_id, end_instrument_id, state_hash, primary_event_hash, account_mode, maintenance_lifecycle_account_state, state, crypto_digest
      FROM state
      WHERE contract_id = ?
      LIMIT 1;
      ```

### DynamoDB Queries using Boto3
Let's convert these queries to DynamoDB operations:

#### 1. Get account state corresponding to a seqNum/transactionId

##### Query 1: Using `transaction_id` as the sort key
```python
import boto3

def get_account_state_by_transaction(contract_id, transaction_id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('YourTableName')
    
    response = table.query(
        KeyConditionExpression=Key('contractId').eq(contract_id) & Key('transactionId').eq(transaction_id),
        Limit=1
    )
    
    return response.get('Items')

# Example usage
items = get_account_state_by_transaction('contractId123', 'transactionId456')
print(items)
```

##### Query 2: Using `seq_num` as the sort key
```python
def get_account_state_by_seqnum(contract_id, seq_num):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('YourTableName')
    
    response = table.query(
        KeyConditionExpression=Key('contractId').eq(contract_id) & Key('seqNum').eq(seq_num),
        Limit=1
    )
    
    return response.get('Items')

# Example usage
items = get_account_state_by_seqnum('contractId123', 789)
print(items)
```

#### 2. Get current account state

```python
def get_current_account_state(contract_id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('YourTableName')
    
    response = table.query(
        KeyConditionExpression=Key('contractId').eq(contract_id),
        Limit=1
    )
    
    return response.get('Items')

# Example usage
items = get_current_account_state('contractId123')
print(items)
```

### Notes:
1. **Replace `YourTableName`** with the actual name of your DynamoDB table.
2. **Key Structure**: Adjust the keys (`transactionId` and `seqNum`) according to your table's actual key schema.
3. **Attributes Projection**: If you need to project specific attributes, you can use the `ProjectionExpression` parameter in the `query` method to specify which attributes to return.

By using these Python functions, you can perform the equivalent of the provided SQL queries on DynamoDB.