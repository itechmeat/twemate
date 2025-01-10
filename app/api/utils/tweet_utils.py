from app.models.tweet_schemas import TweetDetails, TweetAuthor
from loguru import logger

def process_tweet_details(tweet) -> TweetDetails:
    """Convert Twitter API tweet object to TweetDetails model"""
    try:
        if not tweet:
            raise ValueError("Tweet object is None")
            
        # Get display text without @mention if it's a reply
        text = getattr(tweet, 'text', '')
        display_text = text
        if getattr(tweet, 'in_reply_to_status_id', None):
            display_text = ' '.join(word for word in text.split() 
                if not word.startswith('@'))
            
        # Process author information safely
        user = getattr(tweet, 'user', None)
        if not user:
            raise ValueError("Tweet user information is missing")
            
        author = TweetAuthor(
            id=str(getattr(user, 'id', '0')),
            name=getattr(user, 'name', ''),
            username=getattr(user, 'screen_name', ''),
            profile_image_url=getattr(user, 'profile_image_url_https', None)
        )
        
        # Get photo URLs if available
        photo_urls = []
        media = getattr(tweet, 'media', []) or []
        if media:
            photo_urls = [
                item.get('media_url_https') 
                for item in media 
                if isinstance(item, dict) and
                item.get('type') == 'photo' and
                item.get('ext_media_availability', {}).get('status') == 'Available' and
                item.get('media_url_https')
            ]
        
        # Get other attributes safely
        tweet_id = str(getattr(tweet, 'id', '0'))
        created_at = str(getattr(tweet, 'created_at', ''))
        lang = getattr(tweet, 'lang', '')
        retweet_count = getattr(tweet, 'retweet_count', 0)
        favorite_count = getattr(tweet, 'favorite_count', 0)
        
        # Get reply information safely
        in_reply_to_status_id = getattr(tweet, 'in_reply_to_status_id', None)
        in_reply_to_user_id = getattr(tweet, 'in_reply_to_user_id', None)
        in_reply_to_screen_name = getattr(tweet, 'in_reply_to_screen_name', None)
        
        return TweetDetails(
            id=tweet_id,
            text=text,
            display_text=display_text.strip(),
            created_at=created_at,
            lang=lang,
            retweet_count=retweet_count,
            favorite_count=favorite_count,
            author=author,
            in_reply_to_status_id=str(in_reply_to_status_id) if in_reply_to_status_id else None,
            in_reply_to_user_id=str(in_reply_to_user_id) if in_reply_to_user_id else None,
            in_reply_to_screen_name=in_reply_to_screen_name,
            photo_urls=photo_urls
        )
    except Exception as e:
        logger.error(f"Error processing tweet details: {str(e)}")
        logger.debug(f"Tweet object: {tweet}")
        raise 