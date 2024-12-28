from fastapi import APIRouter
from app.api.endpoints import tweets

router = APIRouter()

router.include_router(
    tweets.router,
    prefix="/tweets",
    tags=["tweets"]
) 