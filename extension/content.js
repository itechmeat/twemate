// content.js
const TWEET_SELECTOR =
  '[data-testid="cellInnerDiv"] article[data-testid="tweet"]';
const YOUR_API_ENDPOINT =
  "http://localhost:5678/webhook/3ba5982b-7b97-4cae-9f16-48005600a03f";
const DB_NAME = "TweetsDB";
const DB_VERSION = 1;
const STORE_NAME = "processed_tweets";
let hasProcessedTweets = false; // Flag to track tweet processing

// Initialize IndexedDB
async function initDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => {
      logWithTimestamp("Error opening IndexedDB:", request.error);
      reject(request.error);
    };

    request.onsuccess = () => {
      logWithTimestamp("IndexedDB opened successfully");
      resolve(request.result);
    };

    request.onupgradeneeded = (event) => {
      logWithTimestamp("Creating object store");
      const db = event.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: "id" });
        store.createIndex("timestamp", "timestamp", { unique: false });
      }
    };
  });
}

// Check if tweet was processed
async function isTweetProcessed(tweetId) {
  const db = await initDB();
  return new Promise((resolve) => {
    const transaction = db.transaction([STORE_NAME], "readonly");
    const store = transaction.objectStore(STORE_NAME);
    const request = store.get(tweetId);

    request.onsuccess = () => {
      resolve(Boolean(request.result));
    };

    request.onerror = () => {
      logWithTimestamp("Error checking tweet status:", request.error);
      resolve(false);
    };
  });
}

// Mark tweet as processed
async function markTweetProcessed(tweetId) {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], "readwrite");
    const store = transaction.objectStore(STORE_NAME);

    logWithTimestamp("Attempting to mark tweet as processed:", { tweetId });

    const record = {
      id: tweetId,
      timestamp: new Date().toISOString(),
    };

    const request = store.put(record);

    request.onsuccess = () => {
      logWithTimestamp("Successfully marked tweet as processed:", { tweetId });
      resolve();
    };

    request.onerror = (event) => {
      logWithTimestamp("Error marking tweet as processed:", {
        tweetId,
        error: event.target.error,
      });
      reject(event.target.error);
    };

    transaction.oncomplete = () => {
      logWithTimestamp("Transaction completed for tweet:", { tweetId });
    };

    transaction.onerror = (event) => {
      logWithTimestamp("Transaction error for tweet:", {
        tweetId,
        error: event.target.error,
      });
    };
  });
}

// Clean up old records (keep last 30 days)
async function cleanupOldRecords() {
  const db = await initDB();
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

  const transaction = db.transaction([STORE_NAME], "readwrite");
  const store = transaction.objectStore(STORE_NAME);
  const index = store.index("timestamp");

  const range = IDBKeyRange.upperBound(thirtyDaysAgo.toISOString());
  const request = index.openCursor(range);

  request.onsuccess = (event) => {
    const cursor = event.target.result;
    if (cursor) {
      store.delete(cursor.primaryKey);
      cursor.continue();
    }
  };
}

// Logging function with timestamp
function logWithTimestamp(message, data = null) {
  const timestamp = new Date().toISOString();
  const logMessage = `[Twitter Extension ${timestamp}] ${message}`;

  if (data) {
    console.log(logMessage, data);
  } else {
    console.log(logMessage);
  }
}

// Check if test mode is enabled
function isTestMode() {
  return localStorage.getItem("twitter_extension_test_mode") === "true";
}

// Send POST request to the endpoint
async function sendNotification(notificationData) {
  logWithTimestamp(
    "Attempting to send notification, raw data:",
    notificationData
  );

  try {
    const response = await fetch(YOUR_API_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(notificationData),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    logWithTimestamp("Notification sent successfully:", {
      status: response.status,
      data: notificationData,
    });
  } catch (error) {
    logWithTimestamp("Error sending notification:", {
      error: error.message,
      data: notificationData,
    });
  }
}

// Process single tweet
async function processTweet(tweet) {
  logWithTimestamp("Starting to process tweet element:", tweet);

  // Find tweet link and ID
  const tweetLink = tweet.querySelector('a[href*="/status/"][role="link"]');
  const tweetUrl = tweetLink ? tweetLink.getAttribute("href") : null;
  const tweetId = tweetUrl ? tweetUrl.split("/status/")[1] : null;

  if (!tweetId) {
    logWithTimestamp("Tweet ID not found, skipping");
    return;
  }

  logWithTimestamp("Processing tweet:", { tweetId, url: tweetUrl });

  // Check if tweet was already processed
  const isProcessed = await isTweetProcessed(tweetId);
  logWithTimestamp("Tweet processed status:", {
    tweetId,
    isProcessed,
    testMode: isTestMode(),
  });

  if (isProcessed && !isTestMode()) {
    logWithTimestamp("Tweet already processed, skipping:", tweetId);
    return;
  }

  // Get tweet text content
  const tweetTextElement = tweet.querySelector('[data-testid="tweetText"]');
  const tweetText = tweetTextElement?.textContent || "";

  // Get author information
  const authorUserTag = tweet.querySelector(
    '[data-testid="User-Name"] div[dir="ltr"]'
  );
  const authorName = tweet.querySelector('[id^="id__"] a')?.textContent || "";
  const authorUsername = authorUserTag?.textContent?.replace("@", "") || "";
  const authorAvatar =
    tweet.querySelector('[data-testid="Tweet-User-Avatar"] img')?.src || null;

  // Get tweet metrics
  const replyButton = tweet.querySelector('[data-testid="reply"]');
  const retweetButton = tweet.querySelector('[data-testid="retweet"]');
  const likeButton = tweet.querySelector('[data-testid="like"]');

  const metrics = {
    replies: replyButton?.getAttribute("aria-label")?.match(/\d+/)?.[0] || "0",
    retweets:
      retweetButton?.getAttribute("aria-label")?.match(/\d+/)?.[0] || "0",
    likes: likeButton?.getAttribute("aria-label")?.match(/\d+/)?.[0] || "0",
  };

  // Check for media content
  const hasImages = tweet.querySelector('[data-testid="tweetPhoto"]') !== null;
  const hasVideo = tweet.querySelector('[data-testid="videoPlayer"]') !== null;

  // Compile tweet data
  const tweetData = {
    text: tweetText,
    author: {
      name: authorName,
      username: authorUsername,
      avatar: authorAvatar,
    },
    metrics: metrics,
    media: {
      has_images: hasImages,
      has_video: hasVideo,
    },
    is_reply: Boolean(
      tweet.querySelector('[id^="id__"]')?.textContent?.includes("Replying to")
    ),
    lang: tweetTextElement?.getAttribute("lang") || null,
    created_at: tweet.querySelector("time")?.getAttribute("datetime") || null,
    id: tweetId,
    url: tweetUrl ? `https://twitter.com${tweetUrl}` : null,
    timestamp: new Date().toISOString(),
    test_mode: isTestMode(),
    reprocessed: isProcessed,
  };

  // Send data and mark as processed
  await sendNotification(tweetData);
  if (!isTestMode()) {
    logWithTimestamp("Test mode is OFF, saving to IndexedDB:", { tweetId });
    try {
      await markTweetProcessed(tweetId);
      logWithTimestamp("Successfully saved to IndexedDB:", { tweetId });
    } catch (error) {
      logWithTimestamp("Error saving to IndexedDB:", { tweetId, error });
    }
  } else {
    logWithTimestamp("Test mode is ON, skipping IndexedDB save:", { tweetId });
  }
}

// Process multiple tweets
async function processTweetBatch(tweets) {
  logWithTimestamp(`Processing batch of tweets: ${tweets.length}`);
  for (let i = 0; i < tweets.length; i++) {
    logWithTimestamp(`Processing tweet ${i + 1} of ${tweets.length}`);
    await processTweet(tweets[i]);
  }
}

// Observe DOM for changes
function observeNotifications() {
  logWithTimestamp("Starting observer setup");

  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === "childList" && mutation.addedNodes.length > 0) {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            const tweets = node.querySelectorAll(TWEET_SELECTOR);
            if (tweets.length > 0) {
              logWithTimestamp(`Found ${tweets.length} new tweets in mutation`);
              processTweetBatch(tweets);
            }
          }
        });
      }
    });
  });

  function startObserving() {
    const timelineElement = document.querySelector(
      '[data-testid="primaryColumn"]'
    );

    if (timelineElement) {
      logWithTimestamp("Timeline element found, starting observation");

      observer.observe(timelineElement, {
        childList: true,
        subtree: true,
      });

      // Handle existing tweets only once
      if (!hasProcessedTweets) {
        const initialTweets = timelineElement.querySelectorAll(TWEET_SELECTOR);
        if (initialTweets.length > 0) {
          logWithTimestamp(`Found ${initialTweets.length} initial tweets`);
          processTweetBatch(initialTweets);
          hasProcessedTweets = true;
        }
      }

      // Clean up old records once per hour
      setInterval(cleanupOldRecords, 60 * 60 * 1000);
    } else {
      logWithTimestamp("Timeline element not found, retrying in 1 second");
      setTimeout(startObserving, 1000);
    }
  }

  startObserving();
}

// Initialize extension
logWithTimestamp("Extension initialized");

// Start observing when page is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    logWithTimestamp("DOM Content Loaded - starting observer");
    observeNotifications();
  });
} else {
  logWithTimestamp("Document already loaded - starting observer immediately");
  observeNotifications();
}
