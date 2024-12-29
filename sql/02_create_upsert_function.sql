-- Drop function if it exists
-- DROP FUNCTION IF EXISTS upsert_tweets(jsonb);

CREATE OR REPLACE FUNCTION upsert_tweets(tweets jsonb[])
RETURNS TABLE (
    tweet_id text,
    is_new boolean
) AS $$
BEGIN
    RETURN QUERY
    WITH input_tweets AS (
        SELECT * FROM jsonb_to_recordset(array_to_json(tweets)::jsonb) AS t(
            tweet_id text,
            tweet_user_name text,
            tweet_user_nick text,
            tweet_text text,
            tweet_full_text text,
            tweet_created_at_datetime timestamp,
            tweet_retweet_count integer,
            tweet_likes integer,
            tweet_photo_urls text[],
            tweet_lang text,
            tweet_view_count integer
        )
    ),
    upserted AS (
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
            t.tweet_id,
            t.tweet_user_name,
            t.tweet_user_nick,
            t.tweet_text,
            t.tweet_full_text,
            t.tweet_created_at_datetime,
            t.tweet_retweet_count,
            t.tweet_likes,
            t.tweet_photo_urls,
            t.tweet_lang,
            t.tweet_view_count,
            CURRENT_TIMESTAMP
        FROM input_tweets t
        ON CONFLICT (tweet_id) DO UPDATE 
        SET 
            tweet_retweet_count = EXCLUDED.tweet_retweet_count,
            tweet_likes = EXCLUDED.tweet_likes,
            tweet_view_count = EXCLUDED.tweet_view_count,
            updated_at = CURRENT_TIMESTAMP
        RETURNING tweet_id, (xmax = 0) as is_new
    )
    SELECT tweet_id, is_new FROM upserted;
END;
$$ LANGUAGE plpgsql; 