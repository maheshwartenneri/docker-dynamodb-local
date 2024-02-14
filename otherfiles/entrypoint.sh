#!/bin/bash

# Configure AWS CLI (if installed)
if command -v aws >/dev/null 2>&1; then
  aws configure set endpoint http://localhost:8000
  aws configure set region us-east-1
fi

# Create table (replace with your desired schema)
aws dynamodb create-table \
  --table-name MyTable \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema KeySchemaName=id-key,AttributeName=id,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

# Put item
aws dynamodb put-item \
  --table-name MyTable \
  --item '{"id": {"S": "1"}, "name": {"S": "John Doe"}}'






#dockercompose
version: '3.8'

services:
  dynamodb-local:
    build: .
    volumes:
      - ./data:/data
    ports:
      - "8000:8000"

volumes:
  data:







##dockerfile

FROM amazon/dynamodb-local:latest

# Download and install AWS CLI (optional)
RUN apt-get update && apt-get install -y awscli

# Copy startup script
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]





#dockercompose other 
version: "3.8"

services:
  dynamodb-local:
    image: amazon/dynamodb-local
    ports:
      - "8000:8000"
    volumes:
      - dynamodb-data:/data-dynamodb # Persist data across container restarts
    command: |
      -jar DynamoDBLocal.jar
        -sharedDb
        -tableName MyTable
        -createTable True
        -createSchema '{ "AttributeDefinitions": [{ "AttributeName": "Id", "AttributeType": "S" }], "KeySchema": [{ "AttributeName": "Id", "KeyType": "HASH" }], "ProvisionedThroughput": { "ReadCapacityUnits": 5, "WriteCapacityUnits": 5 } }'
        -putItem '{ "Id": {"S": "item1"}, "Name": {"S": "Item One"} }' # Add more items here if needed

volumes:
  dynamodb-data:


#docker-3

version: "3.8"

services:
  dynamodb-local:
    image: amazon/dynamodb-local
    ports:
      - "8000:8000"
    volumes:
      - dynamodb-data:/data-dynamodb # Persist data across container restarts
    command: >
      -jar DynamoDBLocal.jar
      -sharedDb
      -inMemory
      -optimizeDbBeforeStartup
      -port 8000

  aws-cli:
    image: amazon/aws-cli
    depends_on:
      - dynamodb-local
    volumes:
      - ./scripts:/scripts
    entrypoint: ["/bin/sh", "-c"]
    command: >
      sleep 10 &&
      aws dynamodb create-table \
        --table-name MyTable \
        --attribute-definitions \
            AttributeName=Id,AttributeType=S \
        --key-schema \
            AttributeName=Id,KeyType=HASH \
        --provisioned-throughput \
            ReadCapacityUnits=5,WriteCapacityUnits=5 &&
      aws dynamodb put-item \
        --table-name MyTable \
        --item '{"Id": {"S": "item1"}, "Name": {"S": "Item One"}}'

volumes:
  dynamodb-data:


#docker4

version: "3.8"

services:
  dynamodb-local:
    image: amazon/dynamodb-local
    ports:
      - "8000:8000"
    volumes:
      - dynamodb-data:/data-dynamodb # Persist data across container restarts
    command: >
      -jar DynamoDBLocal.jar
      -sharedDb
      -optimizeDbBeforeStartup
      -dbPath /data-dynamodb
      -port 8000

  aws-cli:
    image: amazon/aws-cli
    depends_on:
      - dynamodb-local
    volumes:
      - ./scripts:/scripts
    entrypoint: ["/bin/sh", "-c"]
    command: >
      sleep 10 &&
      aws dynamodb create-table \
        --table-name MyTable \
        --attribute-definitions \
            AttributeName=Id,AttributeType=S \
        --key-schema \
            AttributeName=Id,KeyType=HASH \
        --provisioned-throughput \
            ReadCapacityUnits=5,WriteCapacityUnits=5 &&
      aws dynamodb put-item \
        --table-name MyTable \
        --item '{"Id": {"S": "item1"}, "Name": {"S": "Item One"}}'

volumes:
  dynamodb-data:


