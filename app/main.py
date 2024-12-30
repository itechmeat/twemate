from fastapi import FastAPI
from app.api.routes import router
from app.api.scheduler import tweet_scheduler
from loguru import logger

app = FastAPI()
app.include_router(router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up the application...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down the application...")
    tweet_scheduler.stop() 