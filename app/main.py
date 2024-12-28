from fastapi import FastAPI
from app.api.routes import router
from app.api.scheduler import scheduled_tweets_fetch
import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = FastAPI()
app.include_router(router)

@app.on_event("startup")
async def start_scheduler():
    asyncio.create_task(scheduled_tweets_fetch()) 