CREATE TABLE IF NOT EXISTS tweets (
    id SERIAL PRIMARY KEY,
    tweet_id BIGINT UNIQUE NOT NULL,
    tweet_user_name TEXT NOT NULL,
    tweet_user_nick TEXT NOT NULL,
    tweet_text TEXT NOT NULL,
    tweet_full_text TEXT NOT NULL,
    tweet_created_at_datetime TIMESTAMP NOT NULL,
    tweet_retweet_count INTEGER DEFAULT 0,
    tweet_likes INTEGER DEFAULT 0,
    tweet_photo_urls TEXT[] DEFAULT NULL,
    tweet_lang TEXT,
    tweet_view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tweets_tweet_id ON tweets(tweet_id);
CREATE INDEX IF NOT EXISTS idx_tweets_created_at ON tweets(created_at); 