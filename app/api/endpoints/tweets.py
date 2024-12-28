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

router = APIRouter()
twitter_client = TwitterClient()

async def handle_twitter_request(request_func):
    try:
        return await request_func()
    except TooManyRequests:
        raise HTTPException(status_code=429, detail="Rate limit reached")
    except Unauthorized:
        await twitter_client.authenticate()
        try:
            return await request_func()
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
    except (AccountLocked, BadRequest, Forbidden, NotFound, TwitterException) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (RequestTimeout, ServerError):
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")

@router.post("/search_tweets", response_model=List[TweetData])
async def search_tweets(params: SearchParams):
    tweet_count = 0
    tweets = None
    results = []

    while tweet_count < params.minimum_tweets:
        async def get_tweets():
            nonlocal tweets
            if tweets is None:
                print(f'{datetime.now()} - Getting tweets...')
                return await twitter_client.client.search_tweet(params.query, product='Latest')
            else:
                wait_time = randint(5, 10)
                print(f'{datetime.now()} - Getting next tweets after {wait_time} seconds ...')
                time.sleep(wait_time)
                return await tweets.next()

        tweets = await handle_twitter_request(get_tweets)
        if not tweets:
            break

        for tweet in tweets:
            tweet_count += 1
            results.append(twitter_client.process_tweet(tweet, tweet_count))
            if tweet_count >= params.minimum_tweets:
                break

    return results

@router.post("/timeline", response_model=List[TweetData])
async def get_user_timeline(params: TimelineParams):
    async def get_timeline():
        return await twitter_client.client.get_timeline(count=params.minimum_tweets)

    tweets = await handle_twitter_request(get_timeline)
    return [
        twitter_client.process_tweet(tweet, i + 1)
        for i, tweet in enumerate(tweets[:params.minimum_tweets])
    ] if tweets else []

@router.post("/latest_timeline", response_model=List[TweetData])
async def get_latest_user_timeline(params: TimelineParams):
    async def get_latest_timeline():
        return await twitter_client.client.get_latest_timeline(count=params.minimum_tweets)

    tweets = await handle_twitter_request(get_latest_timeline)
    return [
        twitter_client.process_tweet(tweet, i + 1)
        for i, tweet in enumerate(tweets[:params.minimum_tweets])
    ] if tweets else [] 