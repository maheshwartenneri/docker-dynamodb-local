limport json
import re

# Define the path to the text file
file_path = 'output_dynamodb_ledger.txt'

# Function to extract DynamoDB queries from a text file
def extract_dynamodb_queries(file_path):
    queries = []
    json_pattern = re.compile(r'{.*?}')  # Regex pattern to identify JSON objects

    with open(file_path, 'r') as file:
        content = file.read()

    # Find all JSON-like strings in the content
    matches = json_pattern.findall(content)

    for match in matches:
        try:
            # Parse the JSON string
            dynamodb_query = json.loads(match)
            queries.append(dynamodb_query)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {match}\nError: {e}")

    return queries

# Call the function to extract the queries
dynamodb_queries = extract_dynamodb_queries(file_path)

if dynamodb_queries:
    print("Extracted DynamoDB Queries:")
    for query in dynamodb_queries:
        print(json.dumps(query, indent=4))
else:
    print("No DynamoDB queries found.")