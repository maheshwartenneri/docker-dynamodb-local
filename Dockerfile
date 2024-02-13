FROM openjdk:8-jre-alpine

WORKDIR /app

# Check if DynamoDB Local is present
RUN if [ ! -f DynamoDBLocal.jar ]; then \
    wget https://s3-us-west-2.amazonaws.com/dynamodb-local/dynamodb_local_latest.tar.gz && \
    tar -xzvf dynamodb_local_latest.tar.gz && \
    rm dynamodb_local_latest.tar.gz; \
fi

EXPOSE 8000

CMD ["java", "-Djava.library.path=./DynamoDBLocal_lib", "-jar", "DynamoDBLocal.jar", "-sharedDb"]
