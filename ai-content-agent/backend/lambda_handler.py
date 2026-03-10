"""
AWS Lambda Handler for Scheduled Instagram Posts

This Lambda function is triggered by EventBridge at scheduled times.
It fetches the post from DynamoDB, publishes to Instagram, and updates status.

Deployment:
1. Package this file with dependencies (boto3, requests)
2. Upload to AWS Lambda
3. Set environment variables
4. Configure EventBridge trigger
5. Set execution role with DynamoDB and EventBridge permissions
"""

import json
import os
import boto3
from datetime import datetime
from typing import Dict, Any


def get_dynamodb_resource():
    """Get DynamoDB resource"""
    return boto3.resource(
        'dynamodb',
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )


def get_scheduled_post(post_id: str) -> Dict:
    """Fetch scheduled post from DynamoDB"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table('ai_content_scheduled_posts')
    
    response = table.get_item(Key={'post_id': post_id})
    return response.get('Item')


def get_content(content_id: str) -> Dict:
    """Fetch content from DynamoDB"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table('ai_content_generated_content')
    
    response = table.get_item(Key={'content_id': content_id})
    return response.get('Item')


def get_campaign(campaign_id: str) -> Dict:
    """Fetch campaign from DynamoDB"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table('ai_content_campaigns')
    
    response = table.get_item(Key={'campaign_id': campaign_id})
    return response.get('Item')


def get_oauth_account(user_id: str, provider: str) -> Dict:
    """Fetch OAuth account from DynamoDB"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table('ai_content_oauth_accounts')
    
    # Query using GSI
    response = table.query(
        IndexName='user_id-index',
        KeyConditionExpression='user_id = :user_id',
        FilterExpression='provider = :provider',
        ExpressionAttributeValues={
            ':user_id': user_id,
            ':provider': provider
        }
    )
    
    items = response.get('Items', [])
    return items[0] if items else None


def get_campaign_assets(campaign_id: str) -> list:
    """Fetch campaign assets from DynamoDB"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table('ai_content_campaign_assets')
    
    response = table.query(
        IndexName='campaign_id-index',
        KeyConditionExpression='campaign_id = :campaign_id',
        ExpressionAttributeValues={':campaign_id': campaign_id}
    )
    
    return response.get('Items', [])


def update_post_status(post_id: str, status: str, **kwargs):
    """Update scheduled post status in DynamoDB"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table('ai_content_scheduled_posts')
    
    update_expr = "SET #status = :status, updated_at = :updated_at"
    expr_values = {
        ':status': status,
        ':updated_at': datetime.utcnow().isoformat()
    }
    expr_names = {'#status': 'status'}
    
    # Add optional fields
    if 'platform_post_id' in kwargs:
        update_expr += ", platform_post_id = :platform_post_id"
        expr_values[':platform_post_id'] = kwargs['platform_post_id']
    
    if 'published_at' in kwargs:
        update_expr += ", published_at = :published_at"
        expr_values[':published_at'] = kwargs['published_at']
    
    if 'error_message' in kwargs:
        update_expr += ", error_message = :error_message"
        expr_values[':error_message'] = kwargs['error_message']
    
    if 'retry_count' in kwargs:
        update_expr += ", retry_count = :retry_count"
        expr_values[':retry_count'] = kwargs['retry_count']
    
    table.update_item(
        Key={'post_id': post_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values
    )


def post_to_instagram(access_token: str, instagram_account_id: str, 
                     caption: str, image_url: str) -> tuple:
    """
    Post to Instagram using Graph API.
    
    Returns:
        Tuple of (success, media_id, error_message)
    """
    import requests
    import time
    
    try:
        # Step 1: Create media container
        print(f"📸 Creating Instagram media container...")
        container_url = f"https://graph.facebook.com/v19.0/{instagram_account_id}/media"
        container_params = {
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token
        }
        
        container_response = requests.post(container_url, params=container_params, timeout=30)
        
        if container_response.status_code != 200:
            error_msg = f"Failed to create container: {container_response.text}"
            print(f"❌ {error_msg}")
            return False, None, error_msg
        
        container_id = container_response.json().get("id")
        print(f"✅ Container created: {container_id}")
        
        # Step 2: Wait for container to be ready
        max_retries = 10
        for attempt in range(max_retries):
            status_url = f"https://graph.facebook.com/v19.0/{container_id}"
            status_params = {
                "fields": "status_code",
                "access_token": access_token
            }
            
            status_response = requests.get(status_url, params=status_params, timeout=30)
            status_code = status_response.json().get("status_code")
            
            if status_code == "FINISHED":
                print(f"✅ Container ready")
                break
            elif status_code == "ERROR":
                return False, None, "Container creation failed"
            
            time.sleep(2)
        
        # Step 3: Publish container
        print(f"🚀 Publishing to Instagram...")
        publish_url = f"https://graph.facebook.com/v19.0/{instagram_account_id}/media_publish"
        publish_params = {
            "creation_id": container_id,
            "access_token": access_token
        }
        
        publish_response = requests.post(publish_url, params=publish_params, timeout=30)
        
        if publish_response.status_code != 200:
            error_msg = f"Failed to publish: {publish_response.text}"
            print(f"❌ {error_msg}")
            return False, None, error_msg
        
        media_id = publish_response.json().get("id")
        print(f"✅ Published! Media ID: {media_id}")
        
        return True, media_id, None
        
    except Exception as e:
        error_msg = f"Exception during posting: {str(e)}"
        print(f"❌ {error_msg}")
        return False, None, error_msg


def handle_scheduled_post(post_id: str) -> Dict[str, Any]:
    """
    Main handler for scheduled Instagram posts.
    
    Args:
        post_id: UUID of the scheduled post
    
    Returns:
        Dict with status and details
    """
    print(f"🚀 Processing scheduled post: {post_id}")
    
    try:
        # Step 1: Fetch scheduled post
        scheduled_post = get_scheduled_post(post_id)
        
        if not scheduled_post:
            error_msg = f"Scheduled post {post_id} not found"
            print(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
        
        # Step 2: Check idempotency - if already posted, skip
        current_status = scheduled_post.get('status')
        if current_status == 'published':
            print(f"✅ Post already published, skipping")
            return {
                'success': True,
                'message': 'Post already published',
                'post_id': post_id
            }
        
        # Step 3: Fetch content
        content_id = scheduled_post.get('content_id')
        content = get_content(content_id)
        
        if not content:
            error_msg = f"Content {content_id} not found"
            print(f"❌ {error_msg}")
            update_post_status(post_id, 'failed', error_message=error_msg)
            return {'success': False, 'error': error_msg}
        
        # Step 4: Fetch campaign
        campaign_id = content.get('campaign_id')
        campaign = get_campaign(campaign_id)
        
        if not campaign:
            error_msg = f"Campaign {campaign_id} not found"
            print(f"❌ {error_msg}")
            update_post_status(post_id, 'failed', error_message=error_msg)
            return {'success': False, 'error': error_msg}
        
        # Step 5: Fetch OAuth account
        user_id = campaign.get('user_id')
        oauth_account = get_oauth_account(user_id, 'instagram')
        
        if not oauth_account:
            error_msg = "Instagram account not connected"
            print(f"❌ {error_msg}")
            update_post_status(post_id, 'failed', error_message=error_msg)
            return {'success': False, 'error': error_msg}
        
        # Step 6: Fetch campaign assets
        assets = get_campaign_assets(campaign_id)
        
        if not assets:
            error_msg = "No images found for campaign"
            print(f"❌ {error_msg}")
            update_post_status(post_id, 'failed', error_message=error_msg)
            return {'success': False, 'error': error_msg}
        
        # Step 7: Get image URL (file_path contains S3 URL)
        image_url = assets[0].get('file_path')
        
        # Step 8: Prepare caption
        caption = content.get('content_text', '')
        hashtags = content.get('hashtags', '')
        full_caption = f"{caption}\n\n{hashtags}" if hashtags else caption
        
        # Step 9: Post to Instagram
        print(f"📤 Posting to Instagram...")
        success, media_id, error = post_to_instagram(
            access_token=oauth_account.get('access_token'),
            instagram_account_id=oauth_account.get('provider_account_id'),
            caption=full_caption,
            image_url=image_url
        )
        
        # Step 10: Update status
        if success:
            update_post_status(
                post_id,
                'published',
                platform_post_id=media_id,
                published_at=datetime.utcnow().isoformat()
            )
            
            print(f"✅ Post published successfully! Media ID: {media_id}")
            
            return {
                'success': True,
                'post_id': post_id,
                'media_id': media_id,
                'published_at': datetime.utcnow().isoformat()
            }
        else:
            # Update with failure
            retry_count = scheduled_post.get('retry_count', 0) + 1
            update_post_status(
                post_id,
                'failed',
                error_message=error,
                retry_count=retry_count
            )
            
            print(f"❌ Post failed: {error}")
            
            return {
                'success': False,
                'post_id': post_id,
                'error': error,
                'retry_count': retry_count
            }
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        
        import traceback
        traceback.print_exc()
        
        # Try to update status
        try:
            update_post_status(post_id, 'failed', error_message=error_msg)
        except:
            pass
        
        return {'success': False, 'error': error_msg}


def lambda_handler(event, context):
    """
    AWS Lambda entry point.
    
    Event format from EventBridge:
    {
        "post_id": "uuid-string"
    }
    """
    print(f"📥 Lambda invoked with event: {json.dumps(event)}")
    
    # Extract post_id from event
    post_id = event.get('post_id')
    
    if not post_id:
        error_msg = "No post_id in event"
        print(f"❌ {error_msg}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': error_msg})
        }
    
    # Process the scheduled post
    result = handle_scheduled_post(post_id)
    
    # Return response
    status_code = 200 if result.get('success') else 500
    
    return {
        'statusCode': status_code,
        'body': json.dumps(result)
    }


# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        'post_id': 'test-post-id'
    }
    
    result = lambda_handler(test_event, None)
    print(f"\nResult: {json.dumps(result, indent=2)}")
