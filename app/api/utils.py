from fastapi import HTTPException
import asyncio
from twikit import (
    TooManyRequests, Unauthorized, TwitterException, 
    BadRequest, Forbidden, NotFound, RequestTimeout, 
    ServerError, AccountLocked
)
from app.api.common import twitter_client
from loguru import logger

ExecutionStopError = (asyncio.CancelledError, KeyboardInterrupt, SystemError)

async def handle_twitter_request(request_func):
    """
    Generic handler for Twitter API requests with error handling and authentication
    
    Args:
        request_func: Async function that makes the actual Twitter API call
        
    Returns:
        The result of the Twitter API call
        
    Raises:
        HTTPException: On various Twitter API errors with appropriate status codes
    """
    try:
        await twitter_client.ensure_authenticated()
        return await request_func()
    except ExecutionStopError:
        raise
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