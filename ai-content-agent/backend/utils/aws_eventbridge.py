"""
AWS EventBridge Scheduling Utility

Manages scheduled events for Instagram post publishing.
Creates EventBridge rules that trigger Lambda functions at specified times.
"""

import boto3
import json
import os
from datetime import datetime
from typing import Tuple, Optional
from botocore.exceptions import ClientError
from config import settings


def get_eventbridge_client():
    """Get boto3 EventBridge client"""
    return boto3.client(
        'events',
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )


def validate_scheduler_config() -> Tuple[bool, Optional[str]]:
    """
    Validate required configuration for EventBridge scheduling.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not settings.AWS_REGION:
        return False, "AWS_REGION not configured"
    
    if not settings.AWS_LAMBDA_POST_HANDLER_ARN:
        return False, "AWS_LAMBDA_POST_HANDLER_ARN not configured - automatic posting cannot be enabled"
    
    return True, None


def create_scheduled_post_rule(post_id: str, scheduled_time: datetime) -> Tuple[bool, Optional[str]]:
    """
    Create an EventBridge rule to trigger Lambda at scheduled time.
    
    Args:
        post_id: UUID of the scheduled post
        scheduled_time: When to trigger the Lambda (UTC datetime)
    
    Returns:
        Tuple of (success, error_message)
    """
    # Validate configuration first
    is_valid, error_msg = validate_scheduler_config()
    if not is_valid:
        print(f"[Scheduler Error] {error_msg}")
        return False, error_msg
    
    eventbridge = get_eventbridge_client()
    lambda_arn = settings.AWS_LAMBDA_POST_HANDLER_ARN
    
    # Rule name format: post-schedule-{post_id}
    rule_name = f"post-schedule-{post_id}"
    
    # Convert datetime to EventBridge cron expression
    # EventBridge doesn't support one-time 'at()' expressions
    # We need to use cron format: cron(minute hour day month ? year)
    # Ensure we're working with UTC time
    if scheduled_time.tzinfo is None:
        # Assume it's already UTC if no timezone info
        utc_time = scheduled_time
    else:
        # Convert to UTC
        utc_time = scheduled_time.utctimetuple()
        utc_time = datetime(*utc_time[:6])
    
    # Create cron expression for one-time execution
    # Format: cron(minute hour day month ? year)
    cron_expr = f"cron({utc_time.minute} {utc_time.hour} {utc_time.day} {utc_time.month} ? {utc_time.year})"
    
    try:
        print(f"[Scheduler] Creating EventBridge rule: {rule_name}")
        print(f"[Scheduler] Schedule expression: {cron_expr}")
        print(f"[Scheduler] Target Lambda: {lambda_arn}")
        
        # Create EventBridge rule
        eventbridge.put_rule(
            Name=rule_name,
            ScheduleExpression=cron_expr,
            State='ENABLED',
            Description=f'Trigger Instagram post {post_id} at {utc_time.isoformat()}'
        )
        
        # Add Lambda as target
        eventbridge.put_targets(
            Rule=rule_name,
            Targets=[
                {
                    'Id': '1',
                    'Arn': lambda_arn,
                    'Input': json.dumps({'post_id': post_id})
                }
            ]
        )
        
        print(f"[Scheduler] EventBridge rule created successfully for post {post_id}")
        return True, None
        
    except ClientError as e:
        error_msg = f"Failed to create EventBridge rule: {str(e)}"
        print(f"[Scheduler Error] {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error creating EventBridge rule: {str(e)}"
        print(f"[Scheduler Error] {error_msg}")
        return False, error_msg


def delete_scheduled_post_rule(post_id: str) -> Tuple[bool, Optional[str]]:
    """
    Delete an EventBridge rule for a scheduled post.
    
    Args:
        post_id: UUID of the scheduled post
    
    Returns:
        Tuple of (success, error_message)
    """
    eventbridge = get_eventbridge_client()
    # Use consistent rule name format
    rule_name = f"post-schedule-{post_id}"
    
    try:
        print(f"[Scheduler] Deleting EventBridge rule: {rule_name}")
        
        # Remove targets first
        eventbridge.remove_targets(
            Rule=rule_name,
            Ids=['1']
        )
        
        # Delete rule
        eventbridge.delete_rule(Name=rule_name)
        
        print(f"[Scheduler] EventBridge rule deleted successfully: {rule_name}")
        return True, None
        
    except ClientError as e:
        # Rule might not exist, which is fine
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"[Scheduler] Rule {rule_name} not found (already deleted)")
            return True, None
        
        error_msg = f"Failed to delete EventBridge rule: {str(e)}"
        print(f"[Scheduler Error] {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error deleting EventBridge rule: {str(e)}"
        print(f"[Scheduler Error] {error_msg}")
        return False, error_msg


def update_scheduled_post_rule(post_id: str, new_scheduled_time: datetime) -> Tuple[bool, Optional[str]]:
    """
    Update the schedule time for an existing EventBridge rule.
    
    Strategy: Delete old rule and create new one to ensure clean state.
    
    Args:
        post_id: UUID of the scheduled post
        new_scheduled_time: New scheduled time (UTC datetime)
    
    Returns:
        Tuple of (success, error_message)
    """
    print(f"[Scheduler] User override detected for post {post_id}")
    print(f"[Scheduler] Updating schedule to: {new_scheduled_time.isoformat()}")
    
    # Delete old rule (ignore errors if it doesn't exist)
    delete_success, delete_error = delete_scheduled_post_rule(post_id)
    
    # Create new rule with updated time
    create_success, create_error = create_scheduled_post_rule(post_id, new_scheduled_time)
    
    if create_success:
        print(f"[Scheduler] EventBridge rule updated successfully for post {post_id}")
        return True, None
    else:
        return False, create_error
