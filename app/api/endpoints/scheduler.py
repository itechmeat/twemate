from fastapi import APIRouter
from app.api.scheduler import tweet_scheduler, SchedulerStartParams
from loguru import logger

router = APIRouter()

@router.post("/start")
async def start_scheduler(
    params: SchedulerStartParams
):
    """Start the tweet scheduler with specified minimum tweets parameter"""
    logger.info(f"Starting scheduler with minimum_tweets={params.minimum_tweets}")
    if tweet_scheduler.start(minimum_tweets=params.minimum_tweets):
        return {
            "status": "success", 
            "message": "Scheduler started",
            "minimum_tweets": params.minimum_tweets
        }
    return {"status": "error", "message": "Scheduler is already running"}

@router.post("/stop")
async def stop_scheduler():
    """Stop the tweet scheduler"""
    if tweet_scheduler.stop():
        return {"status": "success", "message": "Scheduler stopped"}
    return {"status": "error", "message": "Scheduler is not running"} 