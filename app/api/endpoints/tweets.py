from fastapi import APIRouter, HTTPException
from typing import List
import time
from random import randint
from datetime import datetime
from twikit import (
    TooManyRequests, Unauthorized, TwitterException, 
    BadRequest, Forbidden, NotFound, RequestTimeout, 
    ServerError, AccountLocked
)
from app.models.schemas import SearchParams, TimelineParams, TweetData
from app.services.twitter import TwitterClient
from app.services.supabase import supabase
import logging
import random
import asyncio
import os
import json

router = APIRouter()
twitter_client = TwitterClient()
logger = logging.getLogger(__name__)

USE_TWITTER_MOCKS = os.getenv("USE_TWITTER_MOCKS", "false").lower() == "true"

async def handle_twitter_request(request_func):
    try:
        await twitter_client.ensure_authenticated()
        return await request_func()
    except TooManyRequests:
        raise HTTPException(status_code=429, detail="Rate limit reached")
    except Unauthorized:
        # Try to re-authenticate once
        try:
            await twitter_client.authenticate()
            return await request_func()
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
    except (AccountLocked, BadRequest, Forbidden, NotFound, TwitterException) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (RequestTimeout, ServerError):
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")

async def upsert_tweets_batch(tweets_data: List[TweetData]):
    if not tweets_data:
        return None
        
    db_tweets = [{
        "tweet_id": tweet.tweet_id,
        "tweet_user_name": tweet.tweet_user_name,
        "tweet_user_nick": tweet.tweet_user_nick,
        "tweet_text": tweet.text,
        "tweet_full_text": tweet.text,
        "tweet_created_at_datetime": tweet.created_at,
        "tweet_retweet_count": tweet.retweets,
        "tweet_likes": tweet.likes,
        "tweet_photo_urls": "{" + ",".join(f'"{url}"' for url in tweet.photo_urls) + "}" if tweet.photo_urls else None,
        "tweet_lang": tweet.tweet_lang,
        "tweet_view_count": 0,
    } for tweet in tweets_data]
    
    try:
        logger.info(f"Upserting {len(db_tweets)} tweets...")
        response = supabase.rpc(
            'upsert_tweets',
            {'input_tweets': db_tweets}
        ).execute()
        
        if not response.data:
            logger.warning("No response data from upsert operation")
            return True
            
        new_tweets = [
            (row['tweet_id'], tweets_data[i].likes) 
            for i, row in enumerate(response.data) 
            if row['is_new']
        ]
        
        logger.info(f"Found {len(new_tweets)} new tweets")
        
        if new_tweets:
            most_liked_tweet = max(new_tweets, key=lambda x: x[1])
            most_liked_tweet_id = most_liked_tweet[0]
            likes_count = most_liked_tweet[1]
            
            logger.info(f"Selected tweet {most_liked_tweet_id} with {likes_count} likes for favoriting")
            
            delay = random.randint(50, 70)
            logger.info(f"Waiting {delay} seconds before liking tweet {most_liked_tweet_id}")
            await asyncio.sleep(delay)
            
            try:
                await favorite_tweet(most_liked_tweet_id)
                logger.info(f"Successfully queued like for tweet {most_liked_tweet_id}")
            except Exception as e:
                logger.error(f"Failed to like tweet {most_liked_tweet_id}: {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"Error in batch processing tweets: {str(e)}")
        return None

async def fetch_tweets_from_file():
    with open('app/mocks/tweets.json') as f:
        return json.load(f)

async def get_tweets(params: SearchParams | TimelineParams):
    if USE_TWITTER_MOCKS:
        logger.info('Fetching tweets from mock file...')
        return await fetch_tweets_from_file()
    else:
        logger.info('Fetching tweets from Twitter API...')
        if isinstance(params, SearchParams):
            return await twitter_client.client.search_tweet(params.query, product='Latest')
        else:
            return await twitter_client.client.get_timeline()

@router.post("/search_tweets", response_model=List[TweetData])
async def search_tweets(params: SearchParams):
    tweet_count = 0
    tweets = None
    results = []
    batch_size = 100

    while tweet_count < params.minimum_tweets:
        async def get_tweets_func():
            nonlocal tweets
            if tweets is None:
                return await get_tweets(params)
            else:
                wait_time = randint(5, 10)
                logger.info(f'Getting next tweets after {wait_time} seconds ...')
                time.sleep(wait_time)
                return await tweets.next()

        tweets = await handle_twitter_request(get_tweets_func)
        if not tweets:
            break

        batch_tweets = []
        for tweet in tweets:
            tweet_count += 1
            tweet_data = twitter_client.process_tweet(tweet, tweet_count)
            results.append(tweet_data)
            batch_tweets.append(TweetData(**tweet_data))
            
            if len(batch_tweets) >= batch_size or tweet_count >= params.minimum_tweets:
                await upsert_tweets_batch(batch_tweets)
                batch_tweets = []
                
            if tweet_count >= params.minimum_tweets:
                break
        
        if batch_tweets:
            await upsert_tweets_batch(batch_tweets)

    return results

@router.post("/timeline", response_model=List[TweetData])
async def get_user_timeline(params: TimelineParams):
    logger.info("Fetching user timeline...")
    
    async def get_timeline():
        return await get_tweets(params)

    tweets = await handle_twitter_request(get_timeline)
    results = []
    batch_tweets = []

    for i, tweet in enumerate(tweets[:params.minimum_tweets]):
        tweet_data = twitter_client.process_tweet(tweet, i + 1)
        results.append(tweet_data)
        batch_tweets.append(TweetData(**tweet_data))

    if await upsert_tweets_batch(batch_tweets):
        logger.info(f"🐵 Successfully processed {len(results)} tweets from user timeline")
    return results

@router.post("/latest_timeline", response_model=List[TweetData])
async def get_latest_user_timeline(params: TimelineParams):
    logger.info("Fetching latest timeline...")
    
    async def get_latest_timeline():
        return await get_tweets(params)

    tweets = await handle_twitter_request(get_latest_timeline)
    results = []
    batch_tweets = []

    for i, tweet in enumerate(tweets[:params.minimum_tweets]):
        tweet_data = twitter_client.process_tweet(tweet, i + 1)
        results.append(tweet_data)
        batch_tweets.append(TweetData(**tweet_data))

    if await upsert_tweets_batch(batch_tweets):
        logger.info(f"🐶 Successfully processed {len(results)} tweets from latest timeline")
    return results 

@router.post("/favorite_tweet/{tweet_id}")
async def favorite_tweet(tweet_id: int):
    if USE_TWITTER_MOCKS:
        logger.warning("Favorite tweet functionality is disabled in mock mode.")
        raise HTTPException(status_code=403, detail="Favorite tweet functionality is disabled in mock mode.")
    
    logger.info(f"🎯 Attempting to favorite tweet {tweet_id}")
    
    async def do_favorite():
        return await twitter_client.client.favorite_tweet(tweet_id)
    
    try:
        result = await handle_twitter_request(do_favorite)
        logger.info(f"💜 Successfully favorited tweet {tweet_id}")
        return {"status": "success", "tweet_id": tweet_id}
    except Exception as e:
        logger.error(f"Failed to favorite tweet {tweet_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))