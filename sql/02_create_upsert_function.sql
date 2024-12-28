-- Drop function if it exists
-- DROP FUNCTION IF EXISTS upsert_tweets(jsonb);

CREATE OR REPLACE FUNCTION upsert_tweets(tweets jsonb)
RETURNS TABLE (
    tweet_id BIGINT,
    is_new BOOLEAN
) AS $$
DECLARE
    inserted_rows bigint;
BEGIN
    WITH ins AS (
        INSERT INTO tweets (
            tweet_id,
            tweet_user_name,
            tweet_user_nick,
            tweet_text,
            tweet_full_text,
            tweet_created_at_datetime,
            tweet_retweet_count,
            tweet_likes,
            tweet_photo_urls,
            tweet_lang,
            tweet_view_count,
            first_seen_at
        )
        SELECT 
            (value->>'tweet_id')::BIGINT,
            value->>'tweet_user_name',
            value->>'tweet_user_nick',
            value->>'tweet_text',
            value->>'tweet_full_text',
            (value->>'tweet_created_at_datetime')::TIMESTAMP WITH TIME ZONE,
            (value->>'tweet_retweet_count')::INTEGER,
            (value->>'tweet_likes')::INTEGER,
            (value->>'tweet_photo_urls')::TEXT[],
            value->>'tweet_lang',
            (value->>'tweet_view_count')::INTEGER,
            CURRENT_TIMESTAMP
        FROM jsonb_array_elements(tweets)
        ON CONFLICT (tweet_id) DO UPDATE
        SET
            tweet_retweet_count = EXCLUDED.tweet_retweet_count,
            tweet_likes = EXCLUDED.tweet_likes,
            tweet_view_count = EXCLUDED.tweet_view_count
        WHERE tweets.tweet_id = EXCLUDED.tweet_id
        RETURNING tweets.tweet_id
    )
    SELECT 
        i.tweet_id,
        EXISTS (
            SELECT 1 
            FROM tweets t 
            WHERE t.tweet_id = i.tweet_id 
            AND t.first_seen_at >= CURRENT_TIMESTAMP - interval '1 minute'
        ) as is_new
    FROM ins i;
END;
$$ LANGUAGE plpgsql; 