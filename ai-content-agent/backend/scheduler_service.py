"""
Background Scheduler Service

This service runs in the background and automatically posts scheduled content
at the specified times using APScheduler.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
import logging

import dynamodb_client as db
from agents.posting_agent import get_posting_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def post_scheduled_content_job(scheduled_post_id: str):
    """
    Job function that posts a scheduled content piece.
    
    This function is called by APScheduler at the scheduled time.
    
    Args:
        scheduled_post_id: UUID of the scheduled post
    """
    logger.info(f"🚀 Executing scheduled post: {scheduled_post_id}")
    
    try:
        # Fetch scheduled post
        scheduled_post = db.get_scheduled_post(scheduled_post_id)
        
        if not scheduled_post or scheduled_post.get('status') != 'pending':
            logger.warning(f"⚠️  Scheduled post {scheduled_post_id} not found or already processed")
            return
        
        # Get content
        content = db.get_generated_content(scheduled_post['content_id'])
        if not content:
            logger.error(f"❌ Content not found for scheduled post {scheduled_post_id}")
            db.update_scheduled_post(scheduled_post_id, status='failed', error_message='Content not found')
            return
        
        # Get campaign
        campaign = db.get_campaign(content['campaign_id'])
        if not campaign:
            logger.error(f"❌ Campaign not found for content {content['content_id']}")
            db.update_scheduled_post(scheduled_post_id, status='failed', error_message='Campaign not found')
            return
        
        # Get user's OAuth account for the platform
        oauth_account = db.get_oauth_account_by_provider(campaign['user_id'], content['platform'])
        
        if not oauth_account:
            logger.error(f"❌ OAuth account not found for platform {content['platform']}")
            db.update_scheduled_post(scheduled_post_id, status='failed', 
                                    error_message=f"{content['platform']} account not connected")
            return
        
        # Get campaign assets (images)
        assets = db.get_campaign_assets(campaign['campaign_id'])
        
        if not assets and content['platform'] == 'instagram':
            logger.error(f"❌ No images found for campaign {campaign['campaign_id']}")
            db.update_scheduled_post(scheduled_post_id, status='failed', 
                                    error_message='No images found for this campaign')
            return
        
        # Get image URL from S3 (file_path now contains S3 URL)
        image_url = None
        if assets:
            asset = assets[0]
            # file_path now contains the full S3 URL
            image_url = asset['file_path']
            logger.info(f"📸 Using S3 image URL: {image_url}")
        
        # Get posting agent
        posting_agent = get_posting_agent()
        
        # Post to platform
        logger.info(f"📤 Posting to {content['platform']}...")
        
        if content['platform'] == 'instagram':
            success, media_id, error = posting_agent.post_to_instagram(
                access_token=oauth_account['access_token'],
                instagram_account_id=oauth_account['provider_account_id'],
                caption=content['content_text'],
                image_url=image_url,
                hashtags=content.get('hashtags'),
                user_id=campaign['user_id']  # Pass user_id for token refresh
            )
        else:
            logger.warning(f"⚠️  Platform {content['platform']} not yet implemented")
            db.update_scheduled_post(scheduled_post_id, status='failed', 
                                    error_message=f"Platform {content['platform']} not yet implemented")
            return
        
        # Update post status
        if success:
            db.update_scheduled_post(
                scheduled_post_id,
                status='published',
                platform_post_id=media_id,
                published_at=datetime.utcnow()
            )
            logger.info(f"✅ Successfully posted to {content['platform']}! Media ID: {media_id}")
        else:
            retry_count = scheduled_post.get('retry_count', 0) + 1
            db.update_scheduled_post(
                scheduled_post_id,
                status='failed',
                error_message=error,
                retry_count=retry_count
            )
            logger.error(f"❌ Failed to post: {error}")
            
            # Retry logic (up to 3 times)
            if retry_count < 3:
                # Reschedule for 5 minutes later
                retry_time = datetime.utcnow() + timedelta(minutes=5)
                db.update_scheduled_post(scheduled_post_id, scheduled_for=retry_time, status='pending')
                logger.info(f"🔄 Rescheduling for retry at {retry_time}")
                
                # Add new job for retry
                add_scheduled_post_job(scheduled_post_id, retry_time)
        
    except Exception as e:
        logger.error(f"❌ Error executing scheduled post: {e}")
        import traceback
        traceback.print_exc()
        
        # Update status to failed
        try:
            db.update_scheduled_post(
                scheduled_post_id,
                status='failed',
                error_message=str(e),
                retry_count=db.get_scheduled_post(scheduled_post_id).get('retry_count', 0) + 1
            )
        except:
            pass


def add_scheduled_post_job(scheduled_post_id: str, scheduled_time: datetime):
    """
    Add a job to the scheduler for a specific post.
    
    Args:
        scheduled_post_id: UUID of the scheduled post
        scheduled_time: When to post
    """
    global scheduler
    
    if not scheduler:
        logger.error("❌ Scheduler not initialized")
        return
    
    # Create unique job ID
    job_id = f"post_{scheduled_post_id}"
    
    # Check if job already exists
    existing_job = scheduler.get_job(job_id)
    if existing_job:
        logger.info(f"🔄 Updating existing job {job_id}")
        scheduler.reschedule_job(job_id, trigger=DateTrigger(run_date=scheduled_time))
    else:
        logger.info(f"➕ Adding new job {job_id} for {scheduled_time}")
        scheduler.add_job(
            post_scheduled_content_job,
            trigger=DateTrigger(run_date=scheduled_time),
            args=[scheduled_post_id],
            id=job_id,
            replace_existing=True
        )


def remove_scheduled_post_job(scheduled_post_id: str):
    """
    Remove a scheduled job.
    
    Args:
        scheduled_post_id: UUID of the scheduled post
    """
    global scheduler
    
    if not scheduler:
        return
    
    job_id = f"post_{scheduled_post_id}"
    
    try:
        scheduler.remove_job(job_id)
        logger.info(f"🗑️  Removed job {job_id}")
    except:
        pass


def load_pending_posts():
    """
    Load all pending scheduled posts from database and add them to scheduler.
    
    This is called when the scheduler starts to ensure all pending posts
    are scheduled.
    """
    logger.info("📋 Loading pending scheduled posts...")
    
    try:
        # Get all pending posts scheduled for the future
        pending_posts = db.get_pending_scheduled_posts()
        
        logger.info(f"📊 Found {len(pending_posts)} pending posts")
        
        for post in pending_posts:
            scheduled_for = db.deserialize_datetime(post['scheduled_for'])
            add_scheduled_post_job(post['post_id'], scheduled_for)
        
        logger.info(f"✅ Loaded {len(pending_posts)} pending posts into scheduler")
        
    except Exception as e:
        logger.error(f"❌ Error loading pending posts: {e}")
        import traceback
        traceback.print_exc()


def start_scheduler():
    """
    Start the background scheduler service.
    
    This should be called when the FastAPI application starts.
    """
    global scheduler
    
    if scheduler is not None:
        logger.warning("⚠️  Scheduler already running")
        return
    
    logger.info("🚀 Starting background scheduler service...")
    
    # Create scheduler
    scheduler = BackgroundScheduler(
        timezone='UTC',
        job_defaults={
            'coalesce': False,  # Run all missed jobs
            'max_instances': 3  # Allow up to 3 concurrent jobs
        }
    )
    
    # Start scheduler
    scheduler.start()
    logger.info("✅ Scheduler started successfully")
    
    # Load pending posts
    load_pending_posts()
    
    # Add periodic job to check for new pending posts every 5 minutes
    scheduler.add_job(
        load_pending_posts,
        'interval',
        minutes=5,
        id='load_pending_posts',
        replace_existing=True
    )
    
    logger.info("✅ Scheduler service ready")


def stop_scheduler():
    """
    Stop the background scheduler service.
    
    This should be called when the FastAPI application shuts down.
    """
    global scheduler
    
    if scheduler is None:
        return
    
    logger.info("🛑 Stopping scheduler service...")
    scheduler.shutdown()
    scheduler = None
    logger.info("✅ Scheduler stopped")


def get_scheduler_status():
    """
    Get the current status of the scheduler.
    
    Returns:
        dict with scheduler status and job count
    """
    global scheduler
    
    if scheduler is None:
        return {
            "running": False,
            "jobs": 0,
            "message": "Scheduler not started"
        }
    
    jobs = scheduler.get_jobs()
    
    return {
        "running": True,
        "jobs": len(jobs),
        "job_details": [
            {
                "id": job.id,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
            for job in jobs
        ]
    }
