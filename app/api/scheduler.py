import asyncio
import logging
import random
from app.api.endpoints.tweets import get_user_timeline, get_latest_user_timeline
from app.models.schemas import TimelineParams

logger = logging.getLogger(__name__)

async def scheduled_tweets_fetch():
    logger.info("Starting scheduled tweets fetch...")
    while True:
        try:
            params = TimelineParams(minimum_tweets=10)
            
            # get tweets from following users
            latest_tweets = await get_latest_user_timeline(params)
            logger.info(f"🎉 Scheduler: fetched {len(latest_tweets)} latest tweets")
            
            # Random delay between requests (5-7 minutes)
            delay_between_requests = random.randint(300, 420)
            logger.info(f"Waiting {delay_between_requests} seconds before next request...")
            await asyncio.sleep(delay_between_requests)
            
            # get recommended tweets
            user_tweets = await get_user_timeline(params)
            logger.info(f"🎉 Scheduler: fetched {len(user_tweets)} user timeline tweets")

        except Exception as e:
            logger.error(f"Error in scheduled task: {str(e)}")
        
        main_delay = random.randint(1680, 1920)  # 1800 ± 120 seconds
        logger.info(f"Waiting {main_delay} seconds before next cycle...")
        await asyncio.sleep(main_delay) 