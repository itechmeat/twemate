from pydantic import BaseModel, Field
from typing import List

class SearchParams(BaseModel):
    query: str
    minimum_tweets: int = 100
    save_to_db: bool = Field(default=False)

class TimelineParams(BaseModel):
    minimum_tweets: int = 10

class TweetData(BaseModel):
    tweet_id: str
    tweet_user_name: str
    tweet_user_nick: str
    text: str
    created_at: str
    retweets: int
    likes: int
    photo_urls: List[str]
    tweet_lang: str 