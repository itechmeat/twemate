import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

@lru_cache()
def get_twitter_credentials():
    return {
        'username': os.getenv('TWITTER_USERNAME'),
        'email': os.getenv('TWITTER_EMAIL'),
        'password': os.getenv('TWITTER_PASSWORD')
    }