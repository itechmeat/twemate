create or replace function upsert_tweets(tweets jsonb)
returns void
language plpgsql
security definer
as $$
begin
  insert into tweets (
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
    tweet_view_count
  )
  select 
    (tweet->>'tweet_id')::bigint,
    tweet->>'tweet_user_name',
    tweet->>'tweet_user_nick',
    tweet->>'tweet_text',
    tweet->>'tweet_full_text',
    (tweet->>'tweet_created_at_datetime')::timestamp,
    (tweet->>'tweet_retweet_count')::integer,
    (tweet->>'tweet_likes')::integer,
    case 
      when tweet->>'tweet_photo_urls' is null then null
      else (tweet->>'tweet_photo_urls')::text[]
    end,
    tweet->>'tweet_lang',
    (tweet->>'tweet_view_count')::integer
  from jsonb_array_elements(tweets) tweet
  on conflict (tweet_id) do update set
    tweet_user_name = excluded.tweet_user_name,
    tweet_user_nick = excluded.tweet_user_nick,
    tweet_text = excluded.tweet_text,
    tweet_full_text = excluded.tweet_full_text,
    tweet_created_at_datetime = excluded.tweet_created_at_datetime,
    tweet_retweet_count = excluded.tweet_retweet_count,
    tweet_likes = excluded.tweet_likes,
    tweet_photo_urls = excluded.tweet_photo_urls,
    tweet_lang = excluded.tweet_lang,
    tweet_view_count = excluded.tweet_view_count,
    updated_at = CURRENT_TIMESTAMP;
end;
$$; 