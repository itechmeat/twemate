-- Drop function if it exists
-- DROP FUNCTION IF EXISTS upsert_tweets(jsonb);

CREATE OR REPLACE FUNCTION upsert_tweets(input_tweets jsonb[])
RETURNS TABLE (
    tweet_id text,
    is_new boolean
) AS $$
BEGIN
    RETURN QUERY
    WITH tweet_data AS (
        SELECT 
            (tweet->>'tweet_id')::text AS tweet_id,
            tweet->>'tweet_user_name' AS tweet_user_name,
            tweet->>'tweet_user_nick' AS tweet_user_nick,
            tweet->>'tweet_text' AS tweet_text,
            tweet->>'tweet_full_text' AS tweet_full_text,
            (tweet->>'tweet_created_at_datetime')::timestamp AS tweet_created_at_datetime,
            (tweet->>'tweet_retweet_count')::integer AS tweet_retweet_count,
            (tweet->>'tweet_likes')::integer AS tweet_likes,
            CASE 
                WHEN tweet->>'tweet_photo_urls' IS NULL THEN NULL
                ELSE (tweet->>'tweet_photo_urls')::text[]
            END AS tweet_photo_urls,
            tweet->>'tweet_lang' AS tweet_lang,
            (tweet->>'tweet_view_count')::integer AS tweet_view_count,
            CURRENT_TIMESTAMP AS first_seen_at
        FROM jsonb_array_elements(array_to_json(input_tweets)::jsonb) AS tweet
    ),
    upserted AS (
        INSERT INTO tweets AS t
        (
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
            td.tweet_id,
            td.tweet_user_name,
            td.tweet_user_nick,
            td.tweet_text,
            td.tweet_full_text,
            td.tweet_created_at_datetime,
            td.tweet_retweet_count,
            td.tweet_likes,
            td.tweet_photo_urls,
            td.tweet_lang,
            td.tweet_view_count,
            td.first_seen_at
        FROM tweet_data td
        ON CONFLICT ON CONSTRAINT tweets_pkey DO UPDATE
        SET 
            tweet_retweet_count = EXCLUDED.tweet_retweet_count,
            tweet_likes = EXCLUDED.tweet_likes,
            tweet_view_count = EXCLUDED.tweet_view_count,
            updated_at = CURRENT_TIMESTAMP
        RETURNING t.tweet_id, (xmax = 0) AS is_new
    )
    SELECT u.tweet_id, u.is_new FROM upserted u;
END;
$$ LANGUAGE plpgsql;