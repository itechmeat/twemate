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
        
    try:
        logger.info(f"Processing {len(tweets_data)} tweets...")
        
        # Preparing data
        db_tweets = []
        tweet_ids = []
        tweets_map = {}
        
        for tweet in tweets_data:
            db_tweet = {
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
                "tweet_view_count": 0
            }
            db_tweets.append(db_tweet)
            tweet_ids.append(tweet.tweet_id)
            tweets_map[tweet.tweet_id] = db_tweet
            
        # Getting existing tweets in one request
        existing = supabase.table('tweets') \
            .select('tweet_id') \
            .in_('tweet_id', tweet_ids) \
            .execute()
            
        existing_ids = {tweet['tweet_id'] for tweet in existing.data}
        
        # Separating into new and updated tweets
        tweets_to_insert = []
        tweets_to_update = []
        current_time = datetime.now().isoformat()
        
        for tweet in db_tweets:
            if tweet['tweet_id'] in existing_ids:
                tweets_to_update.append(tweet)
            else:
                tweet['first_seen_at'] = current_time
                tweets_to_insert.append(tweet)
        
        # Inserting new tweets in one batch
        if tweets_to_insert:
            supabase.table('tweets') \
                .insert(tweets_to_insert) \
                .execute()
            logger.info(f"Inserted {len(tweets_to_insert)} new tweets")
            
            max_likes_tweet = max(tweets_to_insert, key=lambda tweet: tweet['tweet_likes'], default=None)
            if max_likes_tweet and not USE_TWITTER_MOCKS and random.randint(1, 3) == 1:
                await asyncio.sleep(random.randint(25, 35))
                await favorite_tweet(max_likes_tweet['tweet_id'])

        # Updating existing tweets in one batch
        if tweets_to_update:
            update_data = []
            for tweet in tweets_to_update:
                tweet_id = tweet['tweet_id']
                update_data.append({
                    "tweet_user_name": tweet['tweet_user_name'],
                    "tweet_user_nick": tweet['tweet_user_nick'],
                    "tweet_text": tweet['tweet_text'],
                    "tweet_full_text": tweet['tweet_full_text'],
                    "tweet_created_at_datetime": tweet['tweet_created_at_datetime'],
                    "tweet_retweet_count": tweet['tweet_retweet_count'],
                    "tweet_likes": tweet['tweet_likes'],
                    "tweet_photo_urls": tweet['tweet_photo_urls'],
                    "tweet_lang": tweet['tweet_lang'],
                    "tweet_view_count": tweet['tweet_view_count'],
                    "updated_at": current_time
                })
            supabase.table('tweets') \
                .update(update_data) \
                .in_('tweet_id', [tweet['tweet_id'] for tweet in tweets_to_update]) \
                .execute()
            logger.info(f"Updated {len(tweets_to_update)} existing tweets")
                
        logger.info(f"Successfully processed all {len(tweets_data)} tweets")
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
        elif isinstance(params, TimelineParams):
            # Split requests for timeline and latest_timeline
            if getattr(params, 'is_latest', False):
                return await twitter_client.client.get_latest_timeline()
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
    logger.info("Fetching user timeline (For You)...")
    
    async def get_timeline_tweets():
        if USE_TWITTER_MOCKS:
            return await fetch_tweets_from_file()
        return await twitter_client.client.get_timeline()

    tweets = await handle_twitter_request(get_timeline_tweets)
    results = []
    batch_tweets = []

    for i, tweet in enumerate(tweets[:params.minimum_tweets]):
        tweet_data = twitter_client.process_tweet(tweet, i + 1)
        results.append(tweet_data)
        batch_tweets.append(TweetData(**tweet_data))

    if await upsert_tweets_batch(batch_tweets):
        logger.info(f"🐵 Successfully processed {len(results)} tweets from For You timeline")
    return results

@router.post("/latest_timeline", response_model=List[TweetData])
async def get_latest_user_timeline(params: TimelineParams):
    logger.info("Fetching latest timeline (Following)...")
    
    async def get_latest_timeline_tweets():
        if USE_TWITTER_MOCKS:
            return await fetch_tweets_from_file()
        return await twitter_client.client.get_latest_timeline()

    tweets = await handle_twitter_request(get_latest_timeline_tweets)
    results = []
    batch_tweets = []

    for i, tweet in enumerate(tweets[:params.minimum_tweets]):
        tweet_data = twitter_client.process_tweet(tweet, i + 1)
        results.append(tweet_data)
        batch_tweets.append(TweetData(**tweet_data))

    if await upsert_tweets_batch(batch_tweets):
        logger.info(f"🐶 Successfully processed {len(results)} tweets from Following timeline")
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