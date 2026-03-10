"""
DynamoDB Client Module

Provides reusable DynamoDB client and helper functions for all database operations.
Uses boto3 to interact with AWS DynamoDB service.
"""

import boto3
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError
from config import settings

# Initialize DynamoDB client
dynamodb = boto3.resource(
    'dynamodb',
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
)

# Table names from environment variables
USERS_TABLE = settings.DYNAMODB_TABLE_USERS
OAUTH_ACCOUNTS_TABLE = settings.DYNAMODB_TABLE_OAUTH_ACCOUNTS
CAMPAIGNS_TABLE = settings.DYNAMODB_TABLE_CAMPAIGNS
CAMPAIGN_ASSETS_TABLE = settings.DYNAMODB_TABLE_CAMPAIGN_ASSETS
GENERATED_CONTENT_TABLE = settings.DYNAMODB_TABLE_GENERATED_CONTENT
SCHEDULED_POSTS_TABLE = settings.DYNAMODB_TABLE_SCHEDULED_POSTS
POST_ANALYTICS_TABLE = settings.DYNAMODB_TABLE_POST_ANALYTICS

# Get table references
users_table = dynamodb.Table(USERS_TABLE)
oauth_accounts_table = dynamodb.Table(OAUTH_ACCOUNTS_TABLE)
campaigns_table = dynamodb.Table(CAMPAIGNS_TABLE)
campaign_assets_table = dynamodb.Table(CAMPAIGN_ASSETS_TABLE)
generated_content_table = dynamodb.Table(GENERATED_CONTENT_TABLE)
scheduled_posts_table = dynamodb.Table(SCHEDULED_POSTS_TABLE)
post_analytics_table = dynamodb.Table(POST_ANALYTICS_TABLE)


def serialize_datetime(dt):
    """Convert datetime to ISO format string"""
    if isinstance(dt, datetime):
        return dt.isoformat()
    return dt


def deserialize_datetime(dt_str):
    """Convert ISO format string to datetime"""
    if isinstance(dt_str, str):
        return datetime.fromisoformat(dt_str)
    return dt_str


def python_to_dynamodb(obj):
    """Convert Python types to DynamoDB compatible types"""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: python_to_dynamodb(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [python_to_dynamodb(v) for v in obj]
    return obj


def dynamodb_to_python(obj):
    """Convert DynamoDB types to Python types"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: dynamodb_to_python(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [dynamodb_to_python(v) for v in obj]
    return obj


# ==================== USER OPERATIONS ====================

def create_user(name: str, email: str, hashed_password: str, **kwargs) -> Dict:
    """Create a new user"""
    user_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    item = {
        'user_id': user_id,
        'name': name,
        'email': email,
        'hashed_password': hashed_password,
        'business_name': kwargs.get('business_name'),
        'business_type': kwargs.get('business_type'),
        'is_active': kwargs.get('is_active', True),
        'is_verified': kwargs.get('is_verified', False),
        'created_at': now,
        'updated_at': now
    }
    
    users_table.put_item(Item=python_to_dynamodb(item))
    return dynamodb_to_python(item)


def get_user(user_id: str) -> Optional[Dict]:
    """Get user by ID"""
    try:
        response = users_table.get_item(Key={'user_id': user_id})
        return dynamodb_to_python(response.get('Item'))
    except ClientError:
        return None


def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user by email using GSI"""
    try:
        response = users_table.query(
            IndexName='email-index',
            KeyConditionExpression='email = :email',
            ExpressionAttributeValues={':email': email}
        )
        items = response.get('Items', [])
        return dynamodb_to_python(items[0]) if items else None
    except ClientError:
        return None


def update_user(user_id: str, **kwargs) -> Optional[Dict]:
    """Update user attributes"""
    update_expr = "SET updated_at = :updated_at"
    expr_values = {':updated_at': datetime.utcnow().isoformat()}
    
    for key, value in kwargs.items():
        if value is not None:
            update_expr += f", {key} = :{key}"
            expr_values[f':{key}'] = python_to_dynamodb(value)
    
    try:
        response = users_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
            ReturnValues='ALL_NEW'
        )
        return dynamodb_to_python(response.get('Attributes'))
    except ClientError:
        return None


# ==================== OAUTH OPERATIONS ====================

def create_oauth_account(user_id: str, provider: str, provider_account_id: str,
                        access_token: str, **kwargs) -> Dict:
    """Create OAuth account"""
    oauth_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    item = {
        'oauth_id': oauth_id,
        'user_id': user_id,
        'provider': provider,
        'provider_account_id': provider_account_id,
        'access_token': access_token,
        'refresh_token': kwargs.get('refresh_token'),
        'token_expires_at': serialize_datetime(kwargs.get('token_expires_at')),
        'scope': kwargs.get('scope'),
        'created_at': now,
        'updated_at': now
    }
    
    oauth_accounts_table.put_item(Item=python_to_dynamodb(item))
    return dynamodb_to_python(item)


def get_oauth_account(oauth_id: str) -> Optional[Dict]:
    """Get OAuth account by ID"""
    try:
        response = oauth_accounts_table.get_item(Key={'oauth_id': oauth_id})
        return dynamodb_to_python(response.get('Item'))
    except ClientError:
        return None


def get_oauth_accounts_by_user(user_id: str) -> List[Dict]:
    """Get all OAuth accounts for a user"""
    try:
        response = oauth_accounts_table.query(
            IndexName='user_id-index',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id}
        )
        return [dynamodb_to_python(item) for item in response.get('Items', [])]
    except ClientError:
        return []


def get_oauth_account_by_provider(user_id: str, provider: str) -> Optional[Dict]:
    """Get OAuth account by user and provider"""
    accounts = get_oauth_accounts_by_user(user_id)
    for account in accounts:
        if account.get('provider') == provider:
            return account
    return None


def update_oauth_account(oauth_id: str, **kwargs) -> Optional[Dict]:
    """Update OAuth account"""
    update_expr = "SET updated_at = :updated_at"
    expr_values = {':updated_at': datetime.utcnow().isoformat()}
    
    for key, value in kwargs.items():
        if value is not None:
            update_expr += f", {key} = :{key}"
            expr_values[f':{key}'] = python_to_dynamodb(value)
    
    try:
        response = oauth_accounts_table.update_item(
            Key={'oauth_id': oauth_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
            ReturnValues='ALL_NEW'
        )
        return dynamodb_to_python(response.get('Attributes'))
    except ClientError:
        return None


# ==================== CAMPAIGN OPERATIONS ====================

def create_campaign(user_id: str, name: str, **kwargs) -> Dict:
    """Create a new campaign"""
    campaign_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    item = {
        'campaign_id': campaign_id,
        'user_id': user_id,
        'name': name,
        'description': kwargs.get('description'),
        'status': kwargs.get('status', 'draft'),
        'target_platforms': kwargs.get('target_platforms', {}),
        'campaign_settings': kwargs.get('campaign_settings', {}),
        'start_date': serialize_datetime(kwargs.get('start_date')),
        'end_date': serialize_datetime(kwargs.get('end_date')),
        'created_at': now,
        'updated_at': now
    }
    
    campaigns_table.put_item(Item=python_to_dynamodb(item))
    return dynamodb_to_python(item)


def get_campaign(campaign_id: str) -> Optional[Dict]:
    """Get campaign by ID"""
    try:
        response = campaigns_table.get_item(Key={'campaign_id': campaign_id})
        return dynamodb_to_python(response.get('Item'))
    except ClientError:
        return None


def get_campaigns_by_user(user_id: str) -> List[Dict]:
    """Get all campaigns for a user"""
    try:
        response = campaigns_table.query(
            IndexName='user_id-index',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id}
        )
        return [dynamodb_to_python(item) for item in response.get('Items', [])]
    except ClientError:
        return []


def update_campaign(campaign_id: str, **kwargs) -> Optional[Dict]:
    """Update campaign"""
    update_expr = "SET updated_at = :updated_at"
    expr_values = {':updated_at': datetime.utcnow().isoformat()}
    
    for key, value in kwargs.items():
        if value is not None:
            update_expr += f", {key} = :{key}"
            if key in ['start_date', 'end_date']:
                expr_values[f':{key}'] = serialize_datetime(value)
            else:
                expr_values[f':{key}'] = python_to_dynamodb(value)
    
    try:
        response = campaigns_table.update_item(
            Key={'campaign_id': campaign_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
            ReturnValues='ALL_NEW'
        )
        return dynamodb_to_python(response.get('Attributes'))
    except ClientError:
        return None


def delete_campaign(campaign_id: str) -> bool:
    """Delete campaign"""
    try:
        campaigns_table.delete_item(Key={'campaign_id': campaign_id})
        return True
    except ClientError:
        return False


# ==================== CAMPAIGN ASSET OPERATIONS ====================

def create_campaign_asset(campaign_id: str, asset_type: str, file_name: str,
                         file_path: str, **kwargs) -> Dict:
    """Create campaign asset"""
    asset_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    item = {
        'asset_id': asset_id,
        'campaign_id': campaign_id,
        'asset_type': asset_type,
        'file_name': file_name,
        'file_path': file_path,
        'file_size': kwargs.get('file_size'),
        'mime_type': kwargs.get('mime_type'),
        'asset_metadata': kwargs.get('asset_metadata', {}),
        'created_at': now
    }
    
    campaign_assets_table.put_item(Item=python_to_dynamodb(item))
    return dynamodb_to_python(item)


def get_campaign_assets(campaign_id: str) -> List[Dict]:
    """Get all assets for a campaign"""
    try:
        response = campaign_assets_table.query(
            IndexName='campaign_id-index',
            KeyConditionExpression='campaign_id = :campaign_id',
            ExpressionAttributeValues={':campaign_id': campaign_id}
        )
        return [dynamodb_to_python(item) for item in response.get('Items', [])]
    except ClientError:
        return []


# ==================== GENERATED CONTENT OPERATIONS ====================

def create_generated_content(campaign_id: str, platform: str, content_type: str,
                            content_text: str, **kwargs) -> Dict:
    """Create generated content"""
    content_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    item = {
        'content_id': content_id,
        'campaign_id': campaign_id,
        'platform': platform,
        'content_type': content_type,
        'content_text': content_text,
        'hashtags': kwargs.get('hashtags'),
        'media_urls': kwargs.get('media_urls', {}),
        'ai_model': kwargs.get('ai_model'),
        'ai_metadata': kwargs.get('ai_metadata', {}),
        'status': kwargs.get('status', 'draft'),
        'created_at': now,
        'updated_at': now
    }
    
    generated_content_table.put_item(Item=python_to_dynamodb(item))
    return dynamodb_to_python(item)


def get_generated_content(content_id: str) -> Optional[Dict]:
    """Get generated content by ID"""
    try:
        response = generated_content_table.get_item(Key={'content_id': content_id})
        return dynamodb_to_python(response.get('Item'))
    except ClientError:
        return None


def get_generated_content_by_campaign(campaign_id: str, status: Optional[str] = None) -> List[Dict]:
    """Get all generated content for a campaign"""
    try:
        if status:
            response = generated_content_table.query(
                IndexName='campaign_id-index',
                KeyConditionExpression='campaign_id = :campaign_id',
                FilterExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':campaign_id': campaign_id,
                    ':status': status
                }
            )
        else:
            response = generated_content_table.query(
                IndexName='campaign_id-index',
                KeyConditionExpression='campaign_id = :campaign_id',
                ExpressionAttributeValues={':campaign_id': campaign_id}
            )
        return [dynamodb_to_python(item) for item in response.get('Items', [])]
    except ClientError:
        return []


def update_generated_content(content_id: str, **kwargs) -> Optional[Dict]:
    """Update generated content"""
    update_expr = "SET updated_at = :updated_at"
    expr_values = {':updated_at': datetime.utcnow().isoformat()}
    expr_names = {}
    
    for key, value in kwargs.items():
        if value is not None:
            if key == 'status':
                update_expr += f", #status = :status"
                expr_names['#status'] = 'status'
                expr_values[':status'] = value
            else:
                update_expr += f", {key} = :{key}"
                expr_values[f':{key}'] = python_to_dynamodb(value)
    
    try:
        params = {
            'Key': {'content_id': content_id},
            'UpdateExpression': update_expr,
            'ExpressionAttributeValues': expr_values,
            'ReturnValues': 'ALL_NEW'
        }
        if expr_names:
            params['ExpressionAttributeNames'] = expr_names
            
        response = generated_content_table.update_item(**params)
        return dynamodb_to_python(response.get('Attributes'))
    except ClientError:
        return None


# ==================== SCHEDULED POST OPERATIONS ====================

def create_scheduled_post(content_id: str, scheduled_for: datetime, **kwargs) -> Dict:
    """Create scheduled post"""
    post_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    item = {
        'post_id': post_id,
        'content_id': content_id,
        'scheduled_for': serialize_datetime(scheduled_for),
        'status': kwargs.get('status', 'pending'),
        'platform_post_id': kwargs.get('platform_post_id'),
        'published_at': serialize_datetime(kwargs.get('published_at')),
        'error_message': kwargs.get('error_message'),
        'retry_count': kwargs.get('retry_count', 0),
        'created_at': now,
        'updated_at': now
    }
    
    scheduled_posts_table.put_item(Item=python_to_dynamodb(item))
    return dynamodb_to_python(item)


def get_scheduled_post(post_id: str) -> Optional[Dict]:
    """Get scheduled post by ID"""
    try:
        response = scheduled_posts_table.get_item(Key={'post_id': post_id})
        return dynamodb_to_python(response.get('Item'))
    except ClientError:
        return None


def get_scheduled_posts_by_content(content_id: str) -> List[Dict]:
    """Get all scheduled posts for content"""
    try:
        response = scheduled_posts_table.query(
            IndexName='content_id-index',
            KeyConditionExpression='content_id = :content_id',
            ExpressionAttributeValues={':content_id': content_id}
        )
        return [dynamodb_to_python(item) for item in response.get('Items', [])]
    except ClientError:
        return []


def get_pending_scheduled_posts() -> List[Dict]:
    """Get all pending scheduled posts"""
    try:
        now = datetime.utcnow().isoformat()
        response = scheduled_posts_table.scan(
            FilterExpression='#status = :status AND scheduled_for > :now',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'pending',
                ':now': now
            }
        )
        return [dynamodb_to_python(item) for item in response.get('Items', [])]
    except ClientError:
        return []


def update_scheduled_post(post_id: str, **kwargs) -> Optional[Dict]:
    """Update scheduled post"""
    update_expr = "SET updated_at = :updated_at"
    expr_values = {':updated_at': datetime.utcnow().isoformat()}
    expr_names = {}
    
    for key, value in kwargs.items():
        if value is not None:
            if key == 'status':
                update_expr += f", #status = :status"
                expr_names['#status'] = 'status'
                expr_values[':status'] = value
            elif key in ['scheduled_for', 'published_at']:
                update_expr += f", {key} = :{key}"
                expr_values[f':{key}'] = serialize_datetime(value)
            else:
                update_expr += f", {key} = :{key}"
                expr_values[f':{key}'] = python_to_dynamodb(value)
    
    try:
        params = {
            'Key': {'post_id': post_id},
            'UpdateExpression': update_expr,
            'ExpressionAttributeValues': expr_values,
            'ReturnValues': 'ALL_NEW'
        }
        if expr_names:
            params['ExpressionAttributeNames'] = expr_names
            
        response = scheduled_posts_table.update_item(**params)
        return dynamodb_to_python(response.get('Attributes'))
    except ClientError:
        return None


def delete_scheduled_posts_by_content(content_ids: List[str]) -> bool:
    """Delete scheduled posts for multiple content IDs"""
    try:
        for content_id in content_ids:
            posts = get_scheduled_posts_by_content(content_id)
            for post in posts:
                scheduled_posts_table.delete_item(Key={'post_id': post['post_id']})
        return True
    except ClientError:
        return False


def delete_scheduled_post(post_id: str) -> bool:
    """Delete a single scheduled post"""
    try:
        scheduled_posts_table.delete_item(Key={'post_id': post_id})
        return True
    except ClientError:
        return False


def get_scheduled_posts_by_campaign(campaign_id: str) -> List[Dict]:
    """Get all scheduled posts for a campaign"""
    try:
        # First get all content for the campaign
        content_list = get_generated_content_by_campaign(campaign_id)
        
        # Then get scheduled posts for each content
        all_scheduled = []
        for content in content_list:
            posts = get_scheduled_posts_by_content(content['content_id'])
            all_scheduled.extend(posts)
        
        return all_scheduled
    except ClientError:
        return []


# ==================== POST ANALYTICS OPERATIONS ====================

def create_post_analytics(post_id: str, **kwargs) -> Dict:
    """Create post analytics"""
    analytics_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    item = {
        'analytics_id': analytics_id,
        'post_id': post_id,
        'impressions': kwargs.get('impressions', 0),
        'reach': kwargs.get('reach', 0),
        'likes': kwargs.get('likes', 0),
        'comments': kwargs.get('comments', 0),
        'shares': kwargs.get('shares', 0),
        'saves': kwargs.get('saves', 0),
        'clicks': kwargs.get('clicks', 0),
        'engagement_rate': kwargs.get('engagement_rate', 0.0),
        'analytics_data': kwargs.get('analytics_data', {}),
        'fetched_at': now
    }
    
    post_analytics_table.put_item(Item=python_to_dynamodb(item))
    return dynamodb_to_python(item)


def get_post_analytics(post_id: str) -> Optional[Dict]:
    """Get analytics for a post"""
    try:
        response = post_analytics_table.query(
            IndexName='post_id-index',
            KeyConditionExpression='post_id = :post_id',
            ExpressionAttributeValues={':post_id': post_id}
        )
        items = response.get('Items', [])
        return dynamodb_to_python(items[0]) if items else None
    except ClientError:
        return None


def update_post_analytics(analytics_id: str, **kwargs) -> Optional[Dict]:
    """Update post analytics"""
    update_expr = "SET fetched_at = :fetched_at"
    expr_values = {':fetched_at': datetime.utcnow().isoformat()}
    
    for key, value in kwargs.items():
        if value is not None:
            update_expr += f", {key} = :{key}"
            expr_values[f':{key}'] = python_to_dynamodb(value)
    
    try:
        response = post_analytics_table.update_item(
            Key={'analytics_id': analytics_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
            ReturnValues='ALL_NEW'
        )
        return dynamodb_to_python(response.get('Attributes'))
    except ClientError:
        return None


# ==================== DEPENDENCY INJECTION ====================

def get_db():
    """Dependency for FastAPI routes - returns None for DynamoDB"""
    yield None
