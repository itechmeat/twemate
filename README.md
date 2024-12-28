# TwiMate - AI-agent for Twitter

This service provides a FastAPI-based REST API for interacting with Twitter (X) using the [Twikit library](https://twikit.readthedocs.io/en/latest/twikit.html).

## Features

- Search tweets by query
- Get user's "For You" timeline
- Get user's "Following" timeline
- Photo URLs extraction from tweets
- Error handling and rate limiting
- Docker containerization
- Integration with n8n workflow automation

## Prerequisites

- Docker and Docker Compose
- Twitter (X) account credentials
- n8n network (for n8n integration)

## Installation

1. Clone the repository

2. Install required dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with the following variables:

```bash
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET_KEY=your_twitter_api_secret_key
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
```

4. Create a table and function in Supabase from

- `sql/01_create_tweets_table.sql`
- `sql/02_create_upsert_function.sql`

## Usage

```bash
# For start:
docker-compose up -d --build

# For stop:
docker-compose down
```

The API will be available at http://localhost:4750
Swagger UI will be available at http://localhost:4750/docs
n8n will be available at http://localhost:5678

## API Endpoints

### Search Tweets

```http
POST /search_tweets
Content-Type: application/json

{
    "query": "search query",
    "minimum_tweets": 10
}
```

### Get "For You" Timeline

```http
POST /timeline
Content-Type: application/json

{
    "minimum_tweets": 10
}
```

### Get "Following" Timeline

```http
POST /latest_timeline
Content-Type: application/json

{
    "minimum_tweets": 10
}
```

## Response Format

All endpoints return tweets in the following format:

```json
[
  {
    "tweet_id": "string",
    "tweet_user_name": "string",
    "tweet_user_nick": "string",
    "text": "string",
    "created_at": "string",
    "retweets": 0,
    "likes": 0,
    "photo_urls": ["string"],
    "tweet_lang": "string"
  }
]
```

The tweets are also stored in the database with additional fields:

- `tweet_full_text`: Full text of the tweet
- `tweet_view_count`: Number of views (default 0)
- `created_at`: Timestamp when the tweet was first stored
- `updated_at`: Timestamp of the last update

## Error Handling

The API handles various Twitter-specific errors:

- 429: Rate limit reached
- 401: Authentication failed
- 400: Bad request (includes various Twitter errors)
- 503: Service temporarily unavailable

## Development

The project uses hot-reload in development mode. Any changes to the code will automatically restart the server.

To check the logs:

```bash
docker-compose logs -f twitter-api
```

## Notes

- The service uses Twikit library for Twitter interactions. For more details about available features, check the [Twikit documentation](https://twikit.readthedocs.io/en/latest/twikit.html).
- Make sure to handle your Twitter credentials securely and never commit them to version control.
- The service includes rate limiting and error handling as per Twitter's API guidelines.

## License

This project is licensed under the [MIT License](LICENSE).
