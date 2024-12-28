from datetime import datetime
from twikit import Client
from app.config import get_twitter_credentials

class TwitterClient:
    def __init__(self):
        self.client = Client('en-US')
        self.client.load_cookies('cookies.json')
        self.credentials = get_twitter_credentials()

    async def authenticate(self):
        print(f'{datetime.now()} - Logging in...')
        await self.client.login(
            auth_info_1=self.credentials['username'],
            auth_info_2=self.credentials['email'],
            password=self.credentials['password']
        )
        self.client.save_cookies('cookies.json')

    @staticmethod
    def get_photo_urls(media_list):
        if not media_list:
            return []
        
        return [
            item['media_url_https'] 
            for item in media_list 
            if item.get('type') == 'photo' 
            and item.get('ext_media_availability', {}).get('status') == 'Available'
        ]

    def process_tweet(self, tweet, tweet_count):
        photo_urls = self.get_photo_urls(tweet.media if hasattr(tweet, 'media') else [])
        return {
            'tweet_id': tweet.id,
            'tweet_user_name': tweet.user.name,
            'tweet_user_nick': tweet.user.screen_name,
            'text': tweet.text,
            'created_at': str(tweet.created_at),
            'retweets': tweet.retweet_count,
            'likes': tweet.favorite_count,
            'photo_urls': photo_urls,
            'tweet_lang': tweet.lang,
        } 