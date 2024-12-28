from pydantic import BaseModel
from typing import List

class SearchParams(BaseModel):
    query: str
    minimum_tweets: int = 10

class TimelineParams(BaseModel):
    minimum_tweets: int = 10

class TweetData(BaseModel):
    tweet_id: str
    tweet_count: int
    username: str
    text: str
    created_at: str
    retweets: int
    likes: int
    photo_urls: List[str] 