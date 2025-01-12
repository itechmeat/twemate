import asyncio
import logging
import random
from app.models.schemas import TimelineParams
from loguru import logger
from app.api.common import twitter_client
from pydantic import BaseModel, Field

class SchedulerStartParams(BaseModel):
    minimum_tweets: int = Field(default=10, ge=1, description="Minimum number of tweets to fetch in each request")

class TweetScheduler:
    def __init__(self):
        self.task = None
        self.is_running = False
        self.minimum_tweets = 10

    async def scheduled_tweets_fetch(self):
        self.is_running = True
        logger.info(f"🏁  Starting scheduled tweets fetch with minimum_tweets={self.minimum_tweets}...")
        
        while self.is_running:
            try:
                # Try to ensure authentication
                try:
                    await twitter_client.ensure_authenticated()
                except Exception as e:
                    logger.error(f"Authentication failed: {str(e)}")
                    await asyncio.sleep(32)  # Wait 32 seconds before retrying
                    continue

                params = TimelineParams(minimum_tweets=self.minimum_tweets)
                logger.debug(f"Created TimelineParams with minimum_tweets={params.minimum_tweets}")
                
                # get tweets from following users
                try:
                    from app.api.endpoints.tweets import get_latest_user_timeline, get_user_timeline
                    latest_tweets = await get_latest_user_timeline(params)
                    logger.info(f"🎉  Scheduler: fetched {len(latest_tweets)} latest tweets")
                except Exception as e:
                    logger.error(f"Failed to fetch latest timeline: {str(e)}")
                    await asyncio.sleep(60)
                    continue
                
                # Random delay between requests (5-7 minutes)
                delay_between_requests = random.randint(300, 420)
                logger.info(f"⏳  Waiting {delay_between_requests} seconds before next request...")
                await asyncio.sleep(delay_between_requests)
                
                # get recommended tweets
                try:
                    user_tweets = await get_user_timeline(params)
                    logger.info(f"🎉  Scheduler: fetched {len(user_tweets)} user timeline tweets")
                except Exception as e:
                    logger.error(f"Failed to fetch user timeline: {str(e)}")
                    await asyncio.sleep(60)
                    continue

            except Exception as e:
                logger.error(f"Error in scheduled task: {str(e)}")
                await asyncio.sleep(37)  # 37 seconds delay on error
                continue
            
            main_delay = random.randint(1680, 1920)  # 1800 ± 120 seconds
            logger.info(f"⏳  Waiting {main_delay} seconds before next cycle...")
            await asyncio.sleep(main_delay)

    def start(self, minimum_tweets: int = 10):
        if not self.is_running:
            logger.info(f"Setting minimum_tweets to {minimum_tweets}")
            self.minimum_tweets = minimum_tweets
            self.task = asyncio.create_task(self.scheduled_tweets_fetch())
            logger.info(f"🏁  Tweet scheduler started with minimum_tweets={minimum_tweets}")
            return True
        return False

    def stop(self):
        if self.is_running:
            self.is_running = False
            if self.task:
                self.task.cancel()
            logger.info("🚧  Tweet scheduler stopped")
            return True
        return False

# Create a global instance of the scheduler
tweet_scheduler = TweetScheduler() 