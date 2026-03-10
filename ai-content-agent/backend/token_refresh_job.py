"""
Token Refresh Background Job

This script should be run as a scheduled task (e.g., daily cron job)
to automatically refresh Instagram tokens that are expiring soon.

Usage:
    python token_refresh_job.py

Schedule with cron (daily at 2 AM):
    0 2 * * * cd /path/to/backend && python token_refresh_job.py
"""

from utils.instagram_token_refresh import refresh_all_expiring_tokens
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    logging.info("Starting Instagram token refresh job...")
    
    try:
        summary = refresh_all_expiring_tokens()
        
        logging.info(f"Token refresh job completed: {summary}")
        
        # Exit with error code if any failures
        if summary.get('failed', 0) > 0:
            logging.warning(f"{summary['failed']} tokens failed to refresh")
            exit(1)
        
        exit(0)
        
    except Exception as e:
        logging.error(f"Token refresh job failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
