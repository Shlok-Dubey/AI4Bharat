"""
Check DynamoDB Tables and Data

This script verifies that DynamoDB tables exist and shows their data.
"""

import boto3
from dotenv import load_dotenv
import os
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

# Initialize DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.getenv('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

dynamodb_client = boto3.client(
    'dynamodb',
    region_name=os.getenv('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

def check_tables():
    """Check if all required tables exist"""
    print("🔍 Checking DynamoDB Tables...\n")
    
    required_tables = [
        'ai_content_users',
        'ai_content_oauth_accounts',
        'ai_content_campaigns',
        'ai_content_campaign_assets',
        'ai_content_generated_content',
        'ai_content_scheduled_posts',
        'ai_content_post_analytics'
    ]
    
    try:
        # List all tables
        response = dynamodb_client.list_tables()
        existing_tables = response.get('TableNames', [])
        
        print(f"📊 Total tables in DynamoDB: {len(existing_tables)}\n")
        
        for table_name in required_tables:
            if table_name in existing_tables:
                print(f"✅ {table_name}")
                
                # Get table details
                try:
                    table = dynamodb.Table(table_name)
                    response = table.scan(Limit=1)
                    item_count = response.get('Count', 0)
                    
                    # Get approximate item count
                    table_desc = dynamodb_client.describe_table(TableName=table_name)
                    approx_count = table_desc['Table'].get('ItemCount', 0)
                    
                    print(f"   Items: ~{approx_count}")
                except Exception as e:
                    print(f"   Error reading table: {e}")
            else:
                print(f"❌ {table_name} - NOT FOUND")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False


def show_recent_data():
    """Show recent data from each table"""
    print("\n" + "="*60)
    print("📋 Recent Data")
    print("="*60 + "\n")
    
    tables = {
        'Users': 'ai_content_users',
        'Campaigns': 'ai_content_campaigns',
        'Campaign Assets': 'ai_content_campaign_assets',
        'OAuth Accounts': 'ai_content_oauth_accounts'
    }
    
    for name, table_name in tables.items():
        try:
            table = dynamodb.Table(table_name)
            response = table.scan(Limit=5)
            items = response.get('Items', [])
            
            print(f"{name} ({table_name}):")
            if items:
                print(f"  Found {len(items)} items")
                for item in items:
                    # Show key fields
                    if 'user_id' in item:
                        print(f"    - user_id: {item['user_id']}, email: {item.get('email', 'N/A')}")
                    elif 'campaign_id' in item:
                        print(f"    - campaign_id: {item['campaign_id']}, name: {item.get('name', 'N/A')}")
                    elif 'asset_id' in item:
                        print(f"    - asset_id: {item['asset_id']}, file: {item.get('file_name', 'N/A')}")
                    elif 'oauth_id' in item:
                        print(f"    - oauth_id: {item['oauth_id']}, provider: {item.get('provider', 'N/A')}")
            else:
                print(f"  No items found")
            print()
            
        except Exception as e:
            print(f"  Error: {e}\n")


def check_specific_campaign(campaign_id):
    """Check if a specific campaign exists"""
    print(f"\n🔍 Checking campaign: {campaign_id}")
    
    try:
        table = dynamodb.Table('ai_content_campaigns')
        response = table.get_item(Key={'campaign_id': campaign_id})
        
        if 'Item' in response:
            item = response['Item']
            print(f"✅ Campaign found!")
            print(f"   Name: {item.get('name', 'N/A')}")
            print(f"   User ID: {item.get('user_id', 'N/A')}")
            print(f"   Status: {item.get('status', 'N/A')}")
            print(f"   Created: {item.get('created_at', 'N/A')}")
            return True
        else:
            print(f"❌ Campaign not found in DynamoDB")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("="*60)
    print("DynamoDB Status Check")
    print("="*60 + "\n")
    
    # Check AWS credentials
    print(f"AWS Region: {os.getenv('AWS_REGION', 'us-east-1')}")
    print(f"AWS Access Key: {os.getenv('AWS_ACCESS_KEY_ID', 'NOT SET')[:10]}...")
    print()
    
    # Check tables
    if not check_tables():
        print("\n❌ Failed to check tables. Check AWS credentials.")
        return
    
    # Show recent data
    show_recent_data()
    
    # Check for specific campaign if provided
    import sys
    if len(sys.argv) > 1:
        campaign_id = sys.argv[1]
        check_specific_campaign(campaign_id)
    
    print("\n" + "="*60)
    print("✅ DynamoDB check complete!")
    print("="*60)


if __name__ == "__main__":
    main()
