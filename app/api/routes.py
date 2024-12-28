from fastapi import FastAPI
from app.api.endpoints import tweets

def setup_routes(app: FastAPI):
    app.include_router(tweets.router, tags=["tweets"]) 