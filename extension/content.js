// content.js
const TWEET_SELECTOR =
  '[data-testid="cellInnerDiv"] article[data-testid="tweet"]';
const REPLY_API_ENDPOINT =
  "http://localhost:5678/webhook/3ba5982b-7b97-4cae-9f16-48005600a03f";
const MENTION_WEBHOOK_ENDPOINT =
  "http://localhost:5678/webhook/06ef42be-1d03-4935-9607-9e8dffc1d9a8";
const DB_NAME = "TweetsDB";
const DB_VERSION = 1;
const STORE_NAME = "processed_tweets";
let hasProcessedTweets = false; // Flag to track tweet processing

// Add tweet queue and processing flag
const tweetQueue = new Map();
let isProcessing = false;

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

// Add flag to track processed tweets in memory to prevent duplicates
const processedTweetIds = new Set();

// Add function to get account username
function getAccountUsername() {
  const profileLink = document.querySelector(
    'a[data-testid="AppTabBar_Profile_Link"]'
  );
  return profileLink?.getAttribute("href")?.replace("/", "") || null;
}

// Modify isMention to check for specific account mention
function isMention(tweet) {
  const accountUsername = getAccountUsername();
  if (!accountUsername) {
    logWithTimestamp(
      "Could not determine account username, skipping mention check"
    );
    return false;
  }

  // Check if tweet text contains specific mention
  const tweetText = tweet.querySelector('[data-testid="tweetText"]');
  const mentionPattern = new RegExp(`@${accountUsername}\\b`);
  const hasMention = mentionPattern.test(tweetText?.textContent || "");

  // Verify that mention is an actual link
  const mentionLinks = tweet.querySelectorAll(
    '[data-testid="tweetText"] a[href^="/"][role="link"]'
  );
  const hasMentionLink = Array.from(mentionLinks).some(
    (link) => link.getAttribute("href") === `/${accountUsername}`
  );

  return hasMention && hasMentionLink;
}

// Modify isReply to be independent
function isReply(tweet) {
  const replyingToText = tweet.querySelector(
    '[id^="id__"][style*="color: rgb(113, 118, 123)"]'
  );
  return replyingToText?.textContent.includes("Replying to") || false;
}

// Modify sendNotification to handle different endpoints
async function sendNotification(notificationData, isMentionType = false) {
  const endpoint = isMentionType
    ? MENTION_WEBHOOK_ENDPOINT
    : REPLY_API_ENDPOINT;

  logWithTimestamp(
    `Attempting to send ${
      isMentionType ? "mention" : "reply"
    } notification, raw data:`,
    notificationData
  );

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(notificationData),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    logWithTimestamp(
      `${isMentionType ? "Mention" : "Reply"} notification sent successfully:`,
      {
        status: response.status,
        data: notificationData,
      }
    );
  } catch (error) {
    logWithTimestamp(
      `Error sending ${isMentionType ? "mention" : "reply"} notification:`,
      {
        error: error.message,
        data: notificationData,
      }
    );
  }
}

// Modify processTweet to handle all checks
async function processTweet(tweet) {
  // Find tweet ID first
  const tweetLink = tweet.querySelector('a[href*="/status/"][role="link"]');
  const tweetUrl = tweetLink ? tweetLink.getAttribute("href") : null;
  const tweetId = tweetUrl ? tweetUrl.split("/status/")[1] : null;

  if (!tweetId) {
    logWithTimestamp("Tweet ID not found, skipping");
    return;
  }

  // Check memory cache
  if (processedTweetIds.has(tweetId) && !isTestMode()) {
    logWithTimestamp(
      "Tweet already processed in current session, skipping:",
      tweetId
    );
    return;
  }

  // Check DB cache
  const isProcessed = await isTweetProcessed(tweetId);
  if (isProcessed && !isTestMode()) {
    logWithTimestamp("Tweet already processed in DB, skipping:", tweetId);
    processedTweetIds.add(tweetId); // Add to memory cache to prevent future DB checks
    return;
  }

  // Rest of the processing logic...
  logWithTimestamp("Starting to process tweet element:", tweet);

  const isMentionType = isMention(tweet);
  const isReplyType = !isMentionType && isReply(tweet);

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
    types: {
      is_reply: isReplyType,
      is_mention: isMentionType,
    },
    lang: tweetTextElement?.getAttribute("lang") || null,
    created_at: tweet.querySelector("time")?.getAttribute("datetime") || null,
    id: tweetId,
    url: tweetUrl ? `https://twitter.com${tweetUrl}` : null,
    timestamp: new Date().toISOString(),
    test_mode: isTestMode(),
    reprocessed: isProcessed,
  };

  // Send notifications based on type
  if (isMentionType) {
    await sendNotification(tweetData, true);
  } else if (isReplyType) {
    await sendNotification(tweetData, false);
  }

  // Mark as processed
  if (!isTestMode()) {
    try {
      await markTweetProcessed(tweetId);
      processedTweetIds.add(tweetId);
      logWithTimestamp("Successfully processed and cached tweet:", { tweetId });
    } catch (error) {
      logWithTimestamp("Error marking tweet as processed:", { tweetId, error });
    }
  }
}

// Modify processTweetBatch to use Map
async function processTweetBatch(tweets) {
  // Add new tweets to queue
  tweets.forEach((tweet) => {
    const tweetLink = tweet.querySelector('a[href*="/status/"][role="link"]');
    const tweetUrl = tweetLink?.getAttribute("href");
    const tweetId = tweetUrl?.split("/status/")[1];

    if (tweetId) {
      tweetQueue.set(tweetId, {
        id: tweetId,
        element: tweet,
      });
    }
  });

  // Process queue if not already processing
  if (!isProcessing) {
    await processQueue();
  }
}

// Modify queue processing function to use Map
async function processQueue() {
  if (isProcessing || tweetQueue.size === 0) {
    return;
  }

  isProcessing = true;
  logWithTimestamp(`Processing queue of ${tweetQueue.size} tweets`);

  try {
    for (const [tweetId, { element }] of tweetQueue) {
      // Process tweet without memory cache check
      await processTweet(element);

      // Remove from queue after processing
      tweetQueue.delete(tweetId);
    }
  } catch (error) {
    logWithTimestamp("Error processing queue:", error);
  } finally {
    isProcessing = false;

    // If new items were added during processing, process them
    if (tweetQueue.size > 0) {
      await processQueue();
    }
  }
}

// Modify observer to be more reliable
function observeNotifications() {
  logWithTimestamp("Starting observer setup");

  let debounceTimeout;
  let observationCount = 0;
  let isInitialProcessingDone = false;

  const observer = new MutationObserver((mutations) => {
    observationCount++;
    logWithTimestamp(`Mutation observed #${observationCount}:`, {
      mutationsCount: mutations.length,
    });

    // Clear existing timeout
    if (debounceTimeout) {
      clearTimeout(debounceTimeout);
    }

    // Debounce tweet collection
    debounceTimeout = setTimeout(() => {
      // Get all current tweets on the page
      const currentTweets = new Set(document.querySelectorAll(TWEET_SELECTOR));

      logWithTimestamp("Found tweets on page:", {
        total: currentTweets.size,
        isInitialProcessing: !isInitialProcessingDone,
      });

      if (currentTweets.size > 0) {
        processTweetBatch(Array.from(currentTweets));

        // Mark initial processing as done
        if (!isInitialProcessingDone) {
          isInitialProcessingDone = true;
          logWithTimestamp("Initial tweet processing completed");
        }
      }
    }, 500); // Increased debounce time to 500ms
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

      // Process existing tweets once on startup
      const initialTweets = document.querySelectorAll(TWEET_SELECTOR);
      if (initialTweets.length > 0) {
        logWithTimestamp(`Found ${initialTweets.length} initial tweets`);
        processTweetBatch(Array.from(initialTweets));
        isInitialProcessingDone = true;
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
logWithTimestamp("Extension initialized, account:", getAccountUsername());

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

// Add cleanup for memory cache (e.g., every hour)
setInterval(() => {
  const oneHourAgo = Date.now() - 60 * 60 * 1000;
  processedTweetIds.clear();
  logWithTimestamp("Cleared memory cache of processed tweets");
}, 60 * 60 * 1000);
