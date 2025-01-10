from fastapi import APIRouter
from app.api.endpoints import tweets
from app.api.endpoints import scheduler
from app.api.endpoints import notifications

router = APIRouter()

router.include_router(tweets.router, prefix="/tweets", tags=["tweets"])
router.include_router(scheduler.router, prefix="/scheduler", tags=["scheduler"])
router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])