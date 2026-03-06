#!/usr/bin/env python3
"""
Script to create DynamoDB tables in local DynamoDB for development.
Run this after starting docker-compose to initialize the local database.
"""
import boto3
from botocore.exceptions import ClientError

# Configure local DynamoDB endpoint
dynamodb = boto3.client(
    'dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='us-east-1',
    aws_access_key_id='local',
    aws_secret_access_key='local'
)


def create_table_if_not_exists(table_name, key_schema, attribute_definitions, gsi=None):
    """Create a DynamoDB table if it doesn't already exist."""
    try:
        # Check if table exists
        dynamodb.describe_table(TableName=table_name)
        print(f"✓ Table {table_name} already exists")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            # Table doesn't exist, create it
            print(f"Creating table {table_name}...")
            
            table_config = {
                'TableName': table_name,
                'KeySchema': key_schema,
                'AttributeDefinitions': attribute_definitions,
                'BillingMode': 'PAY_PER_REQUEST'
            }
            
            if gsi:
                table_config['GlobalSecondaryIndexes'] = gsi
            
            dynamodb.create_table(**table_config)
            
            # Wait for table to be created
            waiter = dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            
            print(f"✓ Table {table_name} created successfully")
        else:
            raise


def main():
    """Create all required DynamoDB tables for local development."""
    print("Setting up local DynamoDB tables...\n")
    
    # Users Table
    create_table_if_not_exists(
        table_name='postpilot-dev-users',
        key_schema=[
            {'AttributeName': 'PK', 'KeyType': 'HASH'}
        ],
        attribute_definitions=[
            {'AttributeName': 'PK', 'AttributeType': 'S'}
        ]
    )
    
    # Products Table
    create_table_if_not_exists(
        table_name='postpilot-dev-products',
        key_schema=[
            {'AttributeName': 'PK', 'KeyType': 'HASH'},
            {'AttributeName': 'SK', 'KeyType': 'RANGE'}
        ],
        attribute_definitions=[
            {'AttributeName': 'PK', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'}
        ]
    )
    
    # Campaigns Table with GSI
    create_table_if_not_exists(
        table_name='postpilot-dev-campaigns',
        key_schema=[
            {'AttributeName': 'PK', 'KeyType': 'HASH'},
            {'AttributeName': 'SK', 'KeyType': 'RANGE'}
        ],
        attribute_definitions=[
            {'AttributeName': 'PK', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'},
            {'AttributeName': 'status', 'AttributeType': 'S'},
            {'AttributeName': 'scheduled_time', 'AttributeType': 'N'}
        ],
        gsi=[
            {
                'IndexName': 'StatusScheduledTimeIndex',
                'KeySchema': [
                    {'AttributeName': 'status', 'KeyType': 'HASH'},
                    {'AttributeName': 'scheduled_time', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    )
    
    # Analytics Table
    create_table_if_not_exists(
        table_name='postpilot-dev-analytics',
        key_schema=[
            {'AttributeName': 'PK', 'KeyType': 'HASH'},
            {'AttributeName': 'SK', 'KeyType': 'RANGE'}
        ],
        attribute_definitions=[
            {'AttributeName': 'PK', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'}
        ]
    )
    
    # Memory Table
    create_table_if_not_exists(
        table_name='postpilot-dev-memory',
        key_schema=[
            {'AttributeName': 'PK', 'KeyType': 'HASH'},
            {'AttributeName': 'SK', 'KeyType': 'RANGE'}
        ],
        attribute_definitions=[
            {'AttributeName': 'PK', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'}
        ]
    )
    
    # Rate Limits Table with TTL
    create_table_if_not_exists(
        table_name='postpilot-dev-rate-limits',
        key_schema=[
            {'AttributeName': 'PK', 'KeyType': 'HASH'},
            {'AttributeName': 'SK', 'KeyType': 'RANGE'}
        ],
        attribute_definitions=[
            {'AttributeName': 'PK', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'}
        ]
    )
    
    # Enable TTL on rate limits table
    try:
        dynamodb.update_time_to_live(
            TableName='postpilot-dev-rate-limits',
            TimeToLiveSpecification={
                'Enabled': True,
                'AttributeName': 'expires_at'
            }
        )
        print("✓ TTL enabled on rate-limits table")
    except ClientError as e:
        if 'TimeToLive is already enabled' in str(e):
            print("✓ TTL already enabled on rate-limits table")
        else:
            print(f"⚠ Warning: Could not enable TTL: {e}")
    
    print("\n✅ All tables created successfully!")
    print("\nYou can view tables at: http://localhost:8001")
    print("DynamoDB endpoint: http://localhost:8000")


if __name__ == '__main__':
    main()
