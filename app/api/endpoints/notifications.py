from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.api.common import twitter_client
from app.api.utils import handle_twitter_request
from loguru import logger
import os
from enum import Enum
from app.models.schemas import SearchParams

router = APIRouter()

USE_TWITTER_MOCKS = os.getenv("USE_TWITTER_MOCKS", "false").lower() == "true"

class NotificationType(str, Enum):
    ALL = "All"
    VERIFIED = "Verified"
    MENTIONS = "Mentions"

class NotificationData(BaseModel):
    id: str
    notification_type: Optional[str]
    timestamp: Optional[datetime]
    message: Optional[str]
    icon: Optional[dict]
    from_user: Optional[dict]
    tweet: Optional[dict]

class NotificationMetrics(BaseModel):
    replies: str
    retweets: str
    likes: str

class NotificationMedia(BaseModel):
    has_images: bool
    has_video: bool

class NotificationAuthor(BaseModel):
    name: str
    username: str
    avatar: str

class NotificationPayload(BaseModel):
    text: str
    author: NotificationAuthor
    metrics: NotificationMetrics
    media: NotificationMedia
    is_reply: bool
    lang: str
    created_at: datetime
    id: str
    url: str
    timestamp: datetime
    test_mode: bool = Field(default=False)
    reprocessed: bool = Field(default=False)

class TweetDetails(BaseModel):
    id: str
    text: str
    display_text: str
    created_at: str
    lang: str
    retweet_count: int
    favorite_count: int
    author_name: Optional[str] = None
    author_username: Optional[str] = None
    in_reply_to: Optional[str] = None

@router.get("/", response_model=List[NotificationData])
async def get_notifications(
    notification_type: NotificationType = Query(
        default=NotificationType.ALL,
        description="Type of notifications to fetch"
    ),
    limit: int = Query(default=40, ge=1, le=100, description="Number of notifications to retrieve"),
    cursor: Optional[str] = Query(default=None, description="Cursor for pagination"),
    include_mentions: bool = Query(default=True, description="Include mentions notifications")
):
    """
    Fetch user notifications from Twitter
    
    - notification_type: Type of notifications to fetch (All, Verified, Mentions)
    - limit: Number of notifications to retrieve (1-100, default=40)
    - cursor: Cursor for pagination
    - include_mentions: Whether to include mentions notifications (default: True)
    """
    logger.info(f"🔔  Fetching notifications (type={notification_type}, count={limit}, cursor={cursor}, include_mentions={include_mentions})...")
    
    if USE_TWITTER_MOCKS:
        logger.warning("🚧 Notifications are not available in mock mode")
        return []

    async def fetch_notifications():
        try:
            all_notifications = []
            
            # Get general notifications
            logger.debug(f"📨 Fetching notifications of type: {notification_type.value}")
            notifications = await twitter_client.client.get_notifications(
                type=notification_type.value,
                count=limit,
                cursor=cursor
            )
            
            # Log all messages and attributes
            logger.info("📝 Raw notifications:")
            for notif in notifications:
                logger.info(f"Notification ID: {notif.id}")
                logger.info(f"- Message: {getattr(notif, 'message', 'No message')}")
                logger.info(f"- Type: {notification_type.value}")
                logger.info(f"- Icon: {getattr(notif, 'icon', {})}")
                logger.info(f"- Timestamp: {getattr(notif, 'timestamp_ms', None)}")
                
                # Log tweet information
                if hasattr(notif, 'tweet') and notif.tweet:
                    tweet = notif.tweet
                    logger.info(f"- Tweet raw data: {getattr(tweet, '_data', {})}")
                    if hasattr(tweet, '_data'):
                        data = tweet._data
                        logger.info(f"- Tweet reply info: "
                            f"in_reply_to_status_id={data.get('in_reply_to_status_id')}, "
                            f"in_reply_to_user_id={data.get('in_reply_to_user_id')}, "
                            f"in_reply_to_screen_name={data.get('in_reply_to_screen_name')}")
                
                # Log user information
                if hasattr(notif, 'from_user') and notif.from_user:
                    logger.info(f"- From User: {vars(notif.from_user) if hasattr(notif.from_user, '__dict__') else notif.from_user}")
                
                # Log all available attributes
                logger.info("- All attributes:")
                for attr in dir(notif):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(notif, attr)
                            logger.info(f"  {attr}: {value}")
                        except Exception as e:
                            logger.info(f"  {attr}: Error getting value - {str(e)}")
                logger.info("---")
            
            all_notifications.extend(notifications)
            
            # If needed, get also notifications with mentions
            if include_mentions and notification_type != NotificationType.MENTIONS:
                logger.debug("📨 Fetching mentions notifications")
                mentions = await twitter_client.client.get_notifications(
                    type=NotificationType.MENTIONS.value,
                    count=limit,
                    cursor=cursor
                )
                
                # Log messages from mentions
                logger.info("📝 Raw mentions:")
                for notif in mentions:
                    logger.info(f"Notification ID: {notif.id}")
                    logger.info(f"- Message: {getattr(notif, 'message', 'No message')}")
                    logger.info(f"- Type: Mentions")
                    logger.info(f"- Icon: {getattr(notif, 'icon', {})}")
                    logger.info(f"- Timestamp: {getattr(notif, 'timestamp_ms', None)}")
                    
                    # Log tweet information
                    if hasattr(notif, 'tweet') and notif.tweet:
                        tweet = notif.tweet
                        logger.info(f"- Tweet raw data: {getattr(tweet, '_data', {})}")
                        if hasattr(tweet, '_data'):
                            data = tweet._data
                            logger.info(f"- Tweet reply info: "
                                f"in_reply_to_status_id={data.get('in_reply_to_status_id')}, "
                                f"in_reply_to_user_id={data.get('in_reply_to_user_id')}, "
                                f"in_reply_to_screen_name={data.get('in_reply_to_screen_name')}")
                    
                    # Log user information
                    if hasattr(notif, 'from_user') and notif.from_user:
                        logger.info(f"- From User: {vars(notif.from_user) if hasattr(notif.from_user, '__dict__') else notif.from_user}")
                    
                    # Log all available attributes
                    logger.info("- All attributes:")
                    for attr in dir(notif):
                        if not attr.startswith('_'):
                            try:
                                value = getattr(notif, attr)
                                logger.info(f"  {attr}: {value}")
                            except Exception as e:
                                logger.info(f"  {attr}: Error getting value - {str(e)}")
                    logger.info("---")
                
                all_notifications.extend(mentions)
            
            return all_notifications
        except Exception as e:
            logger.error(f"🚨 Error in fetch_notifications: {str(e)}")
            raise

    try:
        notifications = await handle_twitter_request(fetch_notifications)
        notification_count = len(notifications) if notifications else 0
        logger.info(f"📥  Received {notification_count} notifications from Twitter")
        
        processed_notifications = []
        for notif in notifications:
            try:
                # Get user data
                from_user_data = {}
                if hasattr(notif, 'from_user') and notif.from_user:
                    from_user = notif.from_user
                    from_user_data = {
                        'id': getattr(from_user, 'id', None),
                        'name': getattr(from_user, 'name', None),
                        'screen_name': getattr(from_user, 'screen_name', None)
                    }

                # Get tweet data
                tweet_data = {}
                if hasattr(notif, 'tweet') and notif.tweet:
                    tweet = notif.tweet
                    tweet_data = {
                        'id': getattr(tweet, 'id', None),
                        'text': getattr(tweet, 'text', None),
                        'in_reply_to_status_id': getattr(tweet, 'in_reply_to_status_id', None),
                        'in_reply_to_user_id': getattr(tweet, 'in_reply_to_user_id', None),
                        'in_reply_to_screen_name': getattr(tweet, 'in_reply_to_screen_name', None)
                    }
                    # Add logging for debugging
                    logger.debug(f"Tweet data: in_reply_to_status_id={getattr(tweet, 'in_reply_to_status_id', None)}, "
                                f"in_reply_to_user_id={getattr(tweet, 'in_reply_to_user_id', None)}, "
                                f"in_reply_to_screen_name={getattr(tweet, 'in_reply_to_screen_name', None)}")

                # Convert timestamp_ms to datetime
                timestamp = None
                if hasattr(notif, 'timestamp_ms'):
                    try:
                        timestamp = datetime.fromtimestamp(notif.timestamp_ms / 1000.0)
                    except:
                        timestamp = datetime.now()

                notification_data = {
                    "id": notif.id,
                    "notification_type": notification_type.value,
                    "timestamp": timestamp,
                    "message": getattr(notif, 'message', None),
                    "icon": getattr(notif, 'icon', {}),
                    "from_user": from_user_data,
                    "tweet": tweet_data
                }
                processed_notifications.append(NotificationData(**notification_data))
            except Exception as e:
                logger.error(f"Error processing notification {notif.id}: {str(e)}")
                continue

        logger.info(f"✅  Successfully fetched {len(processed_notifications)} notifications")
        return processed_notifications

    except Exception as e:
        logger.error(f"Failed to fetch notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch notifications: {str(e)}") 

@router.get("/mentions", response_model=List[NotificationData])
async def get_mention_notifications(
    limit: int = Query(default=40, ge=1, le=100, description="Number of notifications to retrieve"),
    cursor: Optional[str] = Query(default=None, description="Cursor for pagination")
):
    """
    Fetch only mention notifications from Twitter
    """
    logger.info(f"🔔  Fetching mention notifications (count={limit}, cursor={cursor})...")
    
    return await get_notifications(
        notification_type=NotificationType.MENTIONS,
        limit=limit,
        cursor=cursor,
        include_mentions=False
    ) 

@router.post("/", response_model=dict)
async def process_notification(
    notification: NotificationPayload = Body(...)
):
    """
    Process incoming notification about a tweet
    """
    try:
        logger.info(f"📨 Received notification for tweet ID: {notification.id}")
        
        async def get_tweet():
            return await twitter_client.client.get_tweet_by_id(notification.id)
            
        if USE_TWITTER_MOCKS:
            logger.warning("🚧 Twitter API calls are disabled in mock mode")
            return {
                "status": "success",
                "message": "Mock mode - skipping Twitter API call",
                "tweet_id": notification.id
            }
            
        tweet = await handle_twitter_request(get_tweet)
        if tweet:
            # Get display text without @mention
            display_text = tweet.text
            if tweet.in_reply_to:
                # If this is a reply, remove @mention from the beginning of the text
                display_text = ' '.join(word for word in tweet.text.split() 
                    if not word.startswith('@'))
            
            tweet_details = TweetDetails(
                id=tweet.id,
                text=tweet.text,  # Original text
                display_text=display_text.strip(),  # Text without @mention
                created_at=tweet.created_at,
                lang=tweet.lang,
                retweet_count=tweet.retweet_count,
                favorite_count=tweet.favorite_count,
                author_name=tweet.user.name if tweet.user else None,
                author_username=tweet.user.screen_name if tweet.user else None,
                in_reply_to=tweet.in_reply_to
            )
            
            return {
                "status": "success",
                "message": "Notification processed successfully",
                "tweet_details": tweet_details.model_dump()
            }
        
        return {
            "status": "success",
            "message": "Tweet not found",
            "tweet_id": notification.id
        }
        
    except Exception as e:
        logger.error(f"Failed to process notification: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process notification: {str(e)}"
        ) 