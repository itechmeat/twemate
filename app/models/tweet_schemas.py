from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TweetAuthor(BaseModel):
    id: str
    name: str
    username: str
    profile_image_url: Optional[str] = None

class TweetDetails(BaseModel):
    id: str
    text: str
    display_text: str
    created_at: str
    lang: str
    retweet_count: int
    favorite_count: int
    author: TweetAuthor
    in_reply_to_status_id: Optional[str] = None
    in_reply_to_user_id: Optional[str] = None
    in_reply_to_screen_name: Optional[str] = None
    in_reply_to: Optional[str] = None
    photo_urls: List[str] = []

class TweetThread(BaseModel):
    main_tweet: TweetDetails
    replies: List[TweetDetails] 

class CreateTweetRequest(BaseModel):
    text: str
    reply_to: Optional[str] = None 