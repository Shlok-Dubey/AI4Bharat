"""
Instagram Token Refresh Utility

Handles automatic refresh of Instagram access tokens before they expire.
Instagram tokens expire after 60 days and must be refreshed.
"""

import requests
from datetime import datetime, timedelta
from typing import Tuple, Optional
import dynamodb_client as db


def refresh_instagram_token(user_id: str) -> Tuple[bool, Optional[str]]:
    """
    Refresh Instagram access token for a user.
    
    This function:
    1. Gets the user's Instagram OAuth account
    2. Checks if token needs refresh (expires in < 7 days)
    3. Calls Instagram API to refresh token
    4. Updates token and expiry in DynamoDB
    
    Args:
        user_id: User ID
    
    Returns:
        Tuple of (success, error_message)
        - (True, None) if refresh successful or not needed
        - (False, error_message) if refresh failed
    
    Example:
        success, error = refresh_instagram_token(user_id)
        if not success:
            print(f"Token refresh failed: {error}")
    """
    # Get user's Instagram OAuth account
    oauth_account = db.get_oauth_account_by_provider(user_id, 'meta')
    
    if not oauth_account:
        return False, "Instagram account not connected"
    
    # Check if token needs refresh
    token_expires_at = oauth_account.get('token_expires_at')
    
    if not token_expires_at:
        # No expiry set, assume needs refresh
        print(f"⚠️  No token expiry set for user {user_id}, refreshing...")
    else:
        # Parse expiry datetime
        if isinstance(token_expires_at, str):
            expiry_dt = datetime.fromisoformat(token_expires_at)
        else:
            expiry_dt = token_expires_at
        
        # Check if expires in less than 7 days
        days_until_expiry = (expiry_dt - datetime.utcnow()).days
        
        if days_until_expiry > 7:
            print(f"✅ Token valid for {days_until_expiry} more days, no refresh needed")
            return True, None
        
        print(f"⚠️  Token expires in {days_until_expiry} days, refreshing...")
    
    # Refresh token via Instagram API
    current_token = oauth_account['access_token']
    
    try:
        # Call Instagram token refresh endpoint
        url = "https://graph.facebook.com/v19.0/refresh_access_token"
        params = {
            'grant_type': 'ig_refresh_token',
            'access_token': current_token
        }
        
        print(f"🔄 Refreshing Instagram token for user {user_id}...")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            error_msg = f"Token refresh failed: {response.text}"
            print(f"❌ {error_msg}")
            
            # Mark account as needing re-authentication
            db.update_oauth_account(
                oauth_account['oauth_id'],
                token_expires_at=datetime.utcnow().isoformat(),  # Mark as expired
                scope='needs_reauth'  # Flag for re-authentication
            )
            
            return False, error_msg
        
        data = response.json()
        
        # Extract new token and expiry
        new_token = data.get('access_token')
        expires_in = data.get('expires_in', 5184000)  # Default 60 days in seconds
        
        if not new_token:
            error_msg = "No access token in refresh response"
            print(f"❌ {error_msg}")
            return False, error_msg
        
        # Calculate new expiry (expires_in is in seconds)
        new_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Update token in DynamoDB
        db.update_oauth_account(
            oauth_account['oauth_id'],
            access_token=new_token,
            token_expires_at=new_expiry.isoformat(),
            scope='active'  # Clear any re-auth flag
        )
        
        print(f"✅ Token refreshed successfully! New expiry: {new_expiry.strftime('%Y-%m-%d')}")
        return True, None
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error during token refresh: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg
    
    except Exception as e:
        error_msg = f"Unexpected error during token refresh: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return False, error_msg


def check_token_validity(oauth_account: dict) -> Tuple[bool, Optional[str]]:
    """
    Check if an Instagram token is valid and not expired.
    
    Args:
        oauth_account: OAuth account dict from DynamoDB
    
    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if token is valid
        - (False, error_message) if token is invalid or expired
    """
    # Check if account needs re-authentication
    if oauth_account.get('scope') == 'needs_reauth':
        return False, "Instagram account needs re-authentication. Please reconnect your account."
    
    # Check token expiry
    token_expires_at = oauth_account.get('token_expires_at')
    
    if not token_expires_at:
        # No expiry set, assume valid but should refresh
        return True, None
    
    # Parse expiry datetime
    if isinstance(token_expires_at, str):
        expiry_dt = datetime.fromisoformat(token_expires_at)
    else:
        expiry_dt = token_expires_at
    
    # Check if expired
    if expiry_dt <= datetime.utcnow():
        return False, "Instagram access token has expired. Please reconnect your account."
    
    return True, None


def refresh_all_expiring_tokens():
    """
    Background job to refresh all tokens expiring in the next 7 days.
    
    This should be run as a scheduled task (e.g., daily cron job).
    
    Returns:
        dict: Summary of refresh operations
    """
    print("🔄 Starting token refresh job...")
    
    # Get all Instagram OAuth accounts
    # Note: This requires scanning the table - in production, consider using a GSI
    try:
        response = db.oauth_accounts_table.scan(
            FilterExpression='provider = :provider',
            ExpressionAttributeValues={':provider': 'meta'}
        )
        
        accounts = [db.dynamodb_to_python(item) for item in response.get('Items', [])]
        
        print(f"📊 Found {len(accounts)} Instagram accounts")
        
        refreshed = 0
        failed = 0
        skipped = 0
        
        for account in accounts:
            user_id = account['user_id']
            
            # Check if needs refresh
            token_expires_at = account.get('token_expires_at')
            if token_expires_at:
                if isinstance(token_expires_at, str):
                    expiry_dt = datetime.fromisoformat(token_expires_at)
                else:
                    expiry_dt = token_expires_at
                
                days_until_expiry = (expiry_dt - datetime.utcnow()).days
                
                if days_until_expiry > 7:
                    skipped += 1
                    continue
            
            # Refresh token
            success, error = refresh_instagram_token(user_id)
            
            if success:
                refreshed += 1
            else:
                failed += 1
                print(f"❌ Failed to refresh token for user {user_id}: {error}")
        
        summary = {
            'total_accounts': len(accounts),
            'refreshed': refreshed,
            'failed': failed,
            'skipped': skipped
        }
        
        print(f"✅ Token refresh job complete: {summary}")
        return summary
        
    except Exception as e:
        print(f"❌ Error in token refresh job: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}
