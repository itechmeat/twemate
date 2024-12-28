import asyncio
import logging
from app.api.endpoints.tweets import get_user_timeline, get_latest_user_timeline
from app.models.schemas import TimelineParams

logger = logging.getLogger(__name__)

async def scheduled_tweets_fetch():
    logger.info("Starting scheduled tweets fetch...")
    while True:
        try:
            params = TimelineParams(minimum_tweets=10)
            user_tweets = await get_user_timeline(params)
            latest_tweets = await get_latest_user_timeline(params)
            
            logger.info(
                f"🎉 Scheduler: fetched {len(user_tweets)} user timeline tweets "
                f"and {len(latest_tweets)} latest tweets"
            )
        except Exception as e:
            logger.error(f"Error in scheduled task: {str(e)}")
        
        await asyncio.sleep(300) 