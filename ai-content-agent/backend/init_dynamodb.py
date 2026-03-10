"""
Initialize DynamoDB Tables

Creates all required tables with proper indexes for the AI Content Agent.
Run this script once to set up the database.
"""

import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

# Initialize DynamoDB client
dynamodb = boto3.client(
    'dynamodb',
    region_name=os.getenv('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)


def create_users_table():
    """Create users table"""
    try:
        dynamodb.create_table(
            TableName='ai_content_users',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'email', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'email-index',
                    'KeySchema': [
                        {'AttributeName': 'email', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print("✅ Created users table")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("⚠️  Users table already exists")
        else:
            print(f"❌ Error creating users table: {e}")



def create_oauth_accounts_table():
    """Create OAuth accounts table"""
    try:
        dynamodb.create_table(
            TableName='ai_content_oauth_accounts',
            KeySchema=[
                {'AttributeName': 'oauth_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'oauth_id', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'user_id-index',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print("✅ Created OAuth accounts table")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("⚠️  OAuth accounts table already exists")
        else:
            print(f"❌ Error creating OAuth accounts table: {e}")


def create_campaigns_table():
    """Create campaigns table"""
    try:
        dynamodb.create_table(
            TableName='ai_content_campaigns',
            KeySchema=[
                {'AttributeName': 'campaign_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'campaign_id', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'user_id-index',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print("✅ Created campaigns table")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("⚠️  Campaigns table already exists")
        else:
            print(f"❌ Error creating campaigns table: {e}")



def create_campaign_assets_table():
    """Create campaign assets table"""
    try:
        dynamodb.create_table(
            TableName='ai_content_campaign_assets',
            KeySchema=[
                {'AttributeName': 'asset_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'asset_id', 'AttributeType': 'S'},
                {'AttributeName': 'campaign_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'campaign_id-index',
                    'KeySchema': [
                        {'AttributeName': 'campaign_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print("✅ Created campaign assets table")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("⚠️  Campaign assets table already exists")
        else:
            print(f"❌ Error creating campaign assets table: {e}")


def create_generated_content_table():
    """Create generated content table"""
    try:
        dynamodb.create_table(
            TableName='ai_content_generated_content',
            KeySchema=[
                {'AttributeName': 'content_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'content_id', 'AttributeType': 'S'},
                {'AttributeName': 'campaign_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'campaign_id-index',
                    'KeySchema': [
                        {'AttributeName': 'campaign_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print("✅ Created generated content table")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("⚠️  Generated content table already exists")
        else:
            print(f"❌ Error creating generated content table: {e}")



def create_scheduled_posts_table():
    """Create scheduled posts table"""
    try:
        dynamodb.create_table(
            TableName='ai_content_scheduled_posts',
            KeySchema=[
                {'AttributeName': 'post_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'post_id', 'AttributeType': 'S'},
                {'AttributeName': 'content_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'content_id-index',
                    'KeySchema': [
                        {'AttributeName': 'content_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print("✅ Created scheduled posts table")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("⚠️  Scheduled posts table already exists")
        else:
            print(f"❌ Error creating scheduled posts table: {e}")


def create_post_analytics_table():
    """Create post analytics table"""
    try:
        dynamodb.create_table(
            TableName='ai_content_post_analytics',
            KeySchema=[
                {'AttributeName': 'analytics_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'analytics_id', 'AttributeType': 'S'},
                {'AttributeName': 'post_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'post_id-index',
                    'KeySchema': [
                        {'AttributeName': 'post_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print("✅ Created post analytics table")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("⚠️  Post analytics table already exists")
        else:
            print(f"❌ Error creating post analytics table: {e}")


if __name__ == "__main__":
    print("🚀 Initializing DynamoDB tables...")
    print()
    
    create_users_table()
    create_oauth_accounts_table()
    create_campaigns_table()
    create_campaign_assets_table()
    create_generated_content_table()
    create_scheduled_posts_table()
    create_post_analytics_table()
    
    print()
    print("✅ DynamoDB initialization complete!")
    print("📊 Tables created with provisioned capacity: 5 RCU / 5 WCU")
    print("💡 You can adjust capacity in AWS Console if needed")
