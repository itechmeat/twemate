from fastapi import APIRouter
from app.api.scheduler import tweet_scheduler
from loguru import logger

router = APIRouter()

@router.post("/start")
async def start_scheduler():
    """Start the tweet scheduler"""
    if tweet_scheduler.start():
        return {"status": "success", "message": "Scheduler started"}
    return {"status": "error", "message": "Scheduler is already running"}

@router.post("/stop")
async def stop_scheduler():
    """Stop the tweet scheduler"""
    if tweet_scheduler.stop():
        return {"status": "success", "message": "Scheduler stopped"}
    return {"status": "error", "message": "Scheduler is not running"} 