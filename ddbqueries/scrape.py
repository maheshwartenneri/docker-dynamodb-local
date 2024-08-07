import json
import re

# Define the path to the text file
file_path = 'output_dynamodb_ledger.txt'

# Function to extract DynamoDB queries from a text file
def extract_dynamodb_queries(file_path):
    queries = []

    # Define a regex pattern to identify JSON objects
    json_pattern = re.compile(r'{.*?}')

    with open(file_path, 'r') as file:
        for line in file:
            # Search for JSON objects in each line
            match = json_pattern.search(line)
            if match:
                json_string = match.group(0)
                try:
                    # Parse the JSON string
                    dynamodb_query = json.loads(json_string)
                    queries.append(dynamodb_query)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON in line: {line}\nError: {e}")

    return queries

# Call the function to extract the queries
dynamodb_queries = extract_dynamodb_queries(file_path)

if dynamodb_queries:
    print("Extracted DynamoDB Queries:")
    for query in dynamodb_queries:
        print(json.dumps(query, indent=4))
else:
    print("No DynamoDB queries found.")