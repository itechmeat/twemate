CREATE TABLE IF NOT EXISTS tweets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tweet_id TEXT UNIQUE NOT NULL,
    tweet_user_name TEXT NOT NULL,
    tweet_user_nick TEXT NOT NULL,
    tweet_text TEXT NOT NULL,
    tweet_full_text TEXT NOT NULL,
    tweet_created_at_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    tweet_retweet_count INTEGER DEFAULT 0,
    tweet_likes INTEGER DEFAULT 0,
    tweet_photo_urls TEXT[] DEFAULT NULL,
    tweet_lang TEXT,
    tweet_in_reply_to TEXT,
    tweet_view_count INTEGER DEFAULT 0,
    is_tweet_liked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tweets_tweet_id ON tweets(tweet_id);
CREATE INDEX IF NOT EXISTS idx_tweets_created_at ON tweets(created_at);
