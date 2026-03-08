# Launch API Documentation

**Version:** 1.0.0  
**Base URL:** `http://localhost:8000`  
**Protocol:** HTTP/REST  
**Format:** JSON

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Authentication](#authentication)
4. [Rate Limits](#rate-limits)
5. [API Endpoints](#api-endpoints)
   - [Health Check](#health-check)
   - [Service Info](#service-info)
   - [Multi-Platform Post](#multi-platform-post)
   - [Platform-Specific Endpoints](#platform-specific-endpoints)
6. [Request/Response Examples](#requestresponse-examples)
7. [Platform-Specific Parameters](#platform-specific-parameters)
8. [Error Codes](#error-codes)
9. [Code Examples](#code-examples)
10. [Retry Logic](#retry-logic)
11. [Best Practices](#best-practices)

---

## Overview

The Launch API is a unified social media posting API that enables posting to 9+ platforms through a single interface. It uses a hybrid architecture:

- **Late.dev API** handles "hard" platforms (Twitter, LinkedIn, Facebook, Instagram, TikTok, YouTube, Pinterest, Threads, Bluesky)
- **Direct API integration** handles "easy" platforms (Reddit, Telegram, Discord, Slack)

### Supported Platforms

| Platform | Integration Method | Requirements |
|----------|-------------------|--------------|
| Twitter/X | Late.dev | LATE_API_KEY |
| LinkedIn | Late.dev | LATE_API_KEY |
| Facebook | Late.dev | LATE_API_KEY |
| Instagram | Late.dev | LATE_API_KEY |
| TikTok | Late.dev | LATE_API_KEY |
| YouTube | Late.dev | LATE_API_KEY |
| Pinterest | Late.dev | LATE_API_KEY |
| Threads | Late.dev | LATE_API_KEY |
| Bluesky | Late.dev | LATE_API_KEY |
| Reddit | Direct (PRAW) | Reddit API credentials |
| Telegram | Bot API | TELEGRAM_BOT_TOKEN |
| Discord | Webhooks | Webhook URLs |
| Slack | Webhooks | Webhook URLs |

---

## Architecture

```
┌─────────────────┐
│  Your App       │
└────────┬────────┘
         │ HTTP POST
         ▼
┌─────────────────┐
│  Launch API     │  localhost:8000
│  (FastAPI)      │
└────┬─────┬──────┘
     │     │
     │     └──────────┐
     │                │
     ▼                ▼
┌─────────┐    ┌──────────────┐
│Late.dev │    │ Direct APIs  │
│API      │    │ (PRAW, etc)  │
└────┬────┘    └──────┬───────┘
     │                │
     ▼                ▼
Hard Platforms    Easy Platforms
(Twitter, LI,     (Reddit, TG,
 FB, IG, TikTok)  Discord, Slack)
```

---

## Authentication

All API endpoints (except `/health` and `/`) require authentication using a Bearer token.

### Authentication Header

```http
Authorization: Bearer YOUR_API_KEY
```

### Configuration

Set your API key in the `.env` file:

```bash
API_KEY=your_secure_api_key_here
```

Default development key: `dev_key`

### Authentication Errors

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | Missing API key | No `Authorization` header provided |
| 403 | Invalid API key | API key doesn't match configured value |

---

## Rate Limits

### Launch API

No built-in rate limiting. Implement rate limiting at the application level.

### Platform Rate Limits

| Platform | Rate Limit | Notes |
|----------|-----------|-------|
| Twitter | 300 tweets/3 hours | Via Late.dev |
| LinkedIn | 100 posts/day | Via Late.dev |
| Reddit | 1 post/10 minutes | Per subreddit (Reddit rule) |
| Telegram | 30 messages/sec | Bot API limit |
| Discord | 30 requests/min | Per webhook |
| Slack | 1 request/sec | Per webhook |

### Best Practices

- Stagger Reddit posts by 10+ minutes between subreddits
- Add delays between Discord/Slack webhook calls
- Use retry logic with exponential backoff (see [Retry Logic](#retry-logic))

---

## API Endpoints

### Health Check

**GET** `/health`

Check if the API server is running.

#### Request

```http
GET /health HTTP/1.1
Host: localhost:8000
```

#### Response

```json
{
  "status": "healthy"
}
```

#### Status Codes

| Code | Description |
|------|-------------|
| 200 | Service is healthy |

---

### Service Info

**GET** `/`

Get service information and supported platforms.

#### Request

```http
GET / HTTP/1.1
Host: localhost:8000
```

#### Response

```json
{
  "service": "Launch API",
  "version": "1.0.0",
  "platforms": {
    "late_dev": [
      "twitter",
      "linkedin",
      "facebook",
      "instagram",
      "tiktok",
      "youtube",
      "pinterest",
      "threads",
      "bluesky"
    ],
    "direct": [
      "reddit",
      "telegram",
      "discord",
      "slack"
    ]
  }
}
```

#### Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |

---

### Multi-Platform Post

**POST** `/post`

Post to multiple platforms in a single request.

#### Request

```http
POST /post HTTP/1.1
Host: localhost:8000
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "text": "Your post content here",
  "platforms": ["twitter", "linkedin", "reddit"],
  "mediaUrls": ["https://example.com/image.jpg"],
  "subreddit": "SaaS",
  "title": "Reddit post title",
  "channel_id": "@yourchannel",
  "webhooks": [
    "https://discord.com/api/webhooks/xxx/yyy",
    "https://hooks.slack.com/services/xxx/yyy/zzz"
  ]
}
```

#### Request Body Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Post content/text |
| `platforms` | array[string] | Yes | List of platforms to post to |
| `mediaUrls` | array[string] | No | URLs of images/videos to attach |
| `subreddit` | string | Conditional* | Subreddit name (required for Reddit) |
| `title` | string | Conditional* | Post title (required for Reddit) |
| `channel_id` | string | Conditional* | Telegram channel ID (required for Telegram) |
| `webhooks` | array[string] | Conditional* | Webhook URLs (required for Discord/Slack) |

*\*Required only when the corresponding platform is included in `platforms`*

#### Response

```json
[
  {
    "success": true,
    "platform": "twitter",
    "post_id": "1234567890",
    "url": "https://twitter.com/user/status/1234567890"
  },
  {
    "success": true,
    "platform": "linkedin",
    "post_id": "abc123",
    "url": "https://linkedin.com/posts/abc123"
  },
  {
    "success": true,
    "platform": "reddit",
    "post_id": "xyz789",
    "url": "https://reddit.com/r/SaaS/comments/xyz789"
  }
]
```

#### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether the post succeeded |
| `platform` | string | Platform name |
| `post_id` | string | Platform-specific post ID |
| `url` | string | URL to the posted content |
| `error` | string | Error message (only on failure) |

#### Status Codes

| Code | Description |
|------|-------------|
| 200 | Posts processed (check individual `success` fields) |
| 401 | Missing authentication |
| 403 | Invalid API key |
| 422 | Invalid request body |

---

### Platform-Specific Endpoints

#### Reddit Only

**POST** `/reddit`

Post to a single subreddit.

##### Request

```http
POST /reddit?subreddit=SaaS&title=My%20Launch&text=Description HTTP/1.1
Host: localhost:8000
Authorization: Bearer YOUR_API_KEY
```

##### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `subreddit` | string | Yes | Subreddit name (without r/) |
| `title` | string | Yes | Post title |
| `text` | string | Yes | Post body text |

##### Response

```json
{
  "success": true,
  "platform": "reddit",
  "post_id": "abc123",
  "url": "https://reddit.com/r/SaaS/comments/abc123"
}
```

---

#### Telegram Only

**POST** `/telegram`

Post to a Telegram channel.

##### Request

```http
POST /telegram?channel_id=@mychannel&text=Message HTTP/1.1
Host: localhost:8000
Authorization: Bearer YOUR_API_KEY
```

##### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channel_id` | string | Yes | Channel ID (@username or -100XXXXXXXXXX) |
| `text` | string | Yes | Message text (supports Markdown) |

##### Response

```json
{
  "success": true,
  "platform": "telegram",
  "post_id": "12345",
  "url": "https://t.me/c/mychannel/12345"
}
```

---

#### Discord Only

**POST** `/discord`

Post to Discord via webhook.

##### Request

```http
POST /discord?webhook_url=https://discord.com/api/webhooks/xxx/yyy&text=Message HTTP/1.1
Host: localhost:8000
Authorization: Bearer YOUR_API_KEY
```

##### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `webhook_url` | string | Yes | Discord webhook URL |
| `text` | string | Yes | Message content |

##### Response

```json
{
  "success": true,
  "platform": "discord"
}
```

---

#### Slack Only

**POST** `/slack`

Post to Slack via webhook.

##### Request

```http
POST /slack?webhook_url=https://hooks.slack.com/services/xxx/yyy/zzz&text=Message HTTP/1.1
Host: localhost:8000
Authorization: Bearer YOUR_API_KEY
```

##### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `webhook_url` | string | Yes | Slack webhook URL |
| `text` | string | Yes | Message content |

##### Response

```json
{
  "success": true,
  "platform": "slack"
}
```

---

## Request/Response Examples

### Example 1: Post to Twitter and LinkedIn

**Request:**

```bash
curl -X POST http://localhost:8000/post \
  -H "Authorization: Bearer dev_key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "🚀 Excited to launch our new product! Check it out at https://example.com",
    "platforms": ["twitter", "linkedin"],
    "mediaUrls": ["https://example.com/launch-image.jpg"]
  }'
```

**Response:**

```json
[
  {
    "success": true,
    "platform": "twitter",
    "post_id": "1234567890",
    "url": "https://twitter.com/user/status/1234567890"
  },
  {
    "success": true,
    "platform": "linkedin",
    "post_id": "abc123",
    "url": "https://linkedin.com/posts/abc123"
  }
]
```

---

### Example 2: Post to Reddit

**Request:**

```bash
curl -X POST http://localhost:8000/post \
  -H "Authorization: Bearer dev_key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I built a tool to automate social media launches. Would love feedback from the community!",
    "platforms": ["reddit"],
    "subreddit": "SaaS",
    "title": "I built a launch automation tool - feedback wanted"
  }'
```

**Response:**

```json
[
  {
    "success": true,
    "platform": "reddit",
    "post_id": "xyz789",
    "url": "https://reddit.com/r/SaaS/comments/xyz789"
  }
]
```

---

### Example 3: Post to All Platforms

**Request:**

```bash
curl -X POST http://localhost:8000/post \
  -H "Authorization: Bearer dev_key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "🚀 Launch day is here!",
    "platforms": ["twitter", "linkedin", "facebook", "instagram", "reddit", "telegram", "discord", "slack"],
    "mediaUrls": ["https://example.com/launch.jpg"],
    "subreddit": "SideProject",
    "title": "Just launched my side project!",
    "channel_id": "@mylaunches",
    "webhooks": [
      "https://discord.com/api/webhooks/123/abc",
      "https://hooks.slack.com/services/T00/B00/XXX"
    ]
  }'
```

**Response:**

```json
[
  {"success": true, "platform": "twitter", "post_id": "111"},
  {"success": true, "platform": "linkedin", "post_id": "222"},
  {"success": true, "platform": "facebook", "post_id": "333"},
  {"success": true, "platform": "instagram", "post_id": "444"},
  {"success": true, "platform": "reddit", "post_id": "555", "url": "https://reddit.com/..."},
  {"success": true, "platform": "telegram", "post_id": "666"},
  {"success": true, "platform": "discord"},
  {"success": true, "platform": "slack"}
]
```

---

### Example 4: Error Response

**Request (missing Reddit fields):**

```bash
curl -X POST http://localhost:8000/post \
  -H "Authorization: Bearer dev_key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Test post",
    "platforms": ["reddit"]
  }'
```

**Response:**

```json
[
  {
    "success": false,
    "platform": "reddit",
    "error": "Reddit requires 'subreddit' and 'title' fields"
  }
]
```

---

## Platform-Specific Parameters

### Late.dev Platforms (Twitter, LinkedIn, Facebook, Instagram, TikTok, etc.)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | string | Yes | Post content |
| `mediaUrls` | array | No | Image/video URLs |

**Notes:**
- Requires `LATE_API_KEY` in environment
- Social accounts must be connected in Late.dev dashboard
- Rate limits vary by platform

---

### Reddit

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `subreddit` | string | Yes | Subreddit name (without r/) |
| `title` | string | Yes | Post title (max 300 chars) |
| `text` | string | Yes | Post body |

**Notes:**
- Requires Reddit API credentials in `.env`
- 10-minute wait between posts to different subreddits
- Follow subreddit rules to avoid bans

---

### Telegram

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channel_id` | string | Yes | Channel ID or @username |
| `text` | string | Yes | Message text (supports Markdown) |

**Channel ID Formats:**
- Public channel: `@channelname`
- Private channel: `-1001234567890`

**Notes:**
- Bot must be admin in the channel
- Supports Markdown formatting

---

### Discord

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `webhooks` | array | Yes | List of webhook URLs |
| `text` | string | Yes | Message content |

**Notes:**
- Create webhooks in channel settings
- Supports markdown and embeds
- No authentication needed (webhook URL contains auth)

---

### Slack

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `webhooks` | array | Yes | List of webhook URLs |
| `text` | string | Yes | Message content |

**Notes:**
- Create incoming webhooks in Slack app settings
- Posts appear from "Launch Bot" with :rocket: icon
- Supports Slack formatting

---

## Error Codes

### HTTP Status Codes

| Code | Description | Action |
|------|-------------|--------|
| 200 | Success | Check `success` field in response |
| 401 | Unauthorized | Add `Authorization` header |
| 403 | Forbidden | Check API key is correct |
| 422 | Validation Error | Check request body format |
| 500 | Server Error | Check server logs |

### Error Response Format

```json
{
  "success": false,
  "platform": "twitter",
  "error": "Late API key not configured"
}
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Missing API key" | No Authorization header | Add `Authorization: Bearer YOUR_KEY` |
| "Invalid API key" | Wrong API key | Check `API_KEY` in `.env` |
| "Late API key not configured" | Missing `LATE_API_KEY` | Add to `.env` |
| "Reddit requires 'subreddit' and 'title' fields" | Missing Reddit params | Add required fields |
| "Telegram requires 'channel_id' field" | Missing channel_id | Add `channel_id` |
| "PRAW not installed" | Missing dependency | Run `pip install praw` |
| "Telegram bot token not configured" | Missing `TELEGRAM_BOT_TOKEN` | Add to `.env` |

---

## Code Examples

### Python

#### Using requests

```python
import requests
import json

API_URL = "http://localhost:8000"
API_KEY = "dev_key"

def post_to_platforms(text, platforms, **kwargs):
    """Post to multiple platforms"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "text": text,
        "platforms": platforms,
        **kwargs
    }
    
    response = requests.post(
        f"{API_URL}/post",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    return response.json()

# Example usage
result = post_to_platforms(
    text="🚀 Launching today!",
    platforms=["twitter", "linkedin"],
    mediaUrls=["https://example.com/image.jpg"]
)

for post in result:
    if post["success"]:
        print(f"✅ Posted to {post['platform']}: {post.get('url', 'OK')}")
    else:
        print(f"❌ Failed on {post['platform']}: {post['error']}")
```

#### Using httpx (async)

```python
import httpx
import asyncio

API_URL = "http://localhost:8000"
API_KEY = "dev_key"

async def post_to_platforms(text, platforms, **kwargs):
    """Post to multiple platforms asynchronously"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "text": text,
        "platforms": platforms,
        **kwargs
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/post",
            headers=headers,
            json=payload,
            timeout=30
        )
        return response.json()

# Example usage
async def main():
    result = await post_to_platforms(
        text="🚀 Launching today!",
        platforms=["twitter", "linkedin", "reddit"],
        subreddit="SaaS",
        title="My new product launch"
    )
    print(result)

asyncio.run(main())
```

#### Reddit Only

```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "dev_key"

def post_to_reddit(subreddit, title, text):
    """Post to Reddit"""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    response = requests.post(
        f"{API_URL}/reddit",
        params={
            "subreddit": subreddit,
            "title": title,
            "text": text
        },
        headers=headers
    )
    
    return response.json()

# Example
result = post_to_reddit(
    subreddit="SaaS",
    title="I built a launch automation tool",
    text="Would love feedback from the community!"
)
print(result)
```

#### Telegram Only

```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "dev_key"

def post_to_telegram(channel_id, text):
    """Post to Telegram channel"""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    response = requests.post(
        f"{API_URL}/telegram",
        params={
            "channel_id": channel_id,
            "text": text
        },
        headers=headers
    )
    
    return response.json()

# Example
result = post_to_telegram(
    channel_id="@mychannel",
    text="🚀 *New Launch!* Check it out [here](https://example.com)"
)
print(result)
```

---

### JavaScript / Node.js

#### Using fetch (Node 18+)

```javascript
const API_URL = 'http://localhost:8000';
const API_KEY = 'dev_key';

async function postToPlatforms(text, platforms, options = {}) {
  const response = await fetch(`${API_URL}/post`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      text,
      platforms,
      ...options
    })
  });

  return response.json();
}

// Example usage
postToPlatforms(
  '🚀 Launching today!',
  ['twitter', 'linkedin'],
  { mediaUrls: ['https://example.com/image.jpg'] }
)
  .then(results => {
    results.forEach(post => {
      if (post.success) {
        console.log(`✅ Posted to ${post.platform}: ${post.url || 'OK'}`);
      } else {
        console.log(`❌ Failed on ${post.platform}: ${post.error}`);
      }
    });
  })
  .catch(console.error);
```

#### Using axios

```javascript
const axios = require('axios');

const API_URL = 'http://localhost:8000';
const API_KEY = 'dev_key';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
  }
});

async function postToPlatforms(text, platforms, options = {}) {
  try {
    const response = await api.post('/post', {
      text,
      platforms,
      ...options
    });
    return response.data;
  } catch (error) {
    console.error('API Error:', error.response?.data || error.message);
    throw error;
  }
}

// Example usage
async function launch() {
  const results = await postToPlatforms(
    '🚀 Launching today!',
    ['twitter', 'linkedin', 'reddit'],
    {
      subreddit: 'SaaS',
      title: 'My new product launch',
      mediaUrls: ['https://example.com/launch.jpg']
    }
  );

  results.forEach(post => {
    console.log(`${post.success ? '✅' : '❌'} ${post.platform}`);
  });
}

launch();
```

#### Reddit Only

```javascript
const axios = require('axios');

const API_URL = 'http://localhost:8000';
const API_KEY = 'dev_key';

async function postToReddit(subreddit, title, text) {
  const response = await axios.post(
    `${API_URL}/reddit`,
    null,
    {
      params: { subreddit, title, text },
      headers: { 'Authorization': `Bearer ${API_KEY}` }
    }
  );
  return response.data;
}

// Example
postToReddit(
  'SaaS',
  'I built a launch automation tool',
  'Would love feedback!'
)
  .then(result => console.log(result))
  .catch(console.error);
```

#### Discord Only

```javascript
const axios = require('axios');

const API_URL = 'http://localhost:8000';
const API_KEY = 'dev_key';

async function postToDiscord(webhookUrl, text) {
  const response = await axios.post(
    `${API_URL}/discord`,
    null,
    {
      params: { webhook_url: webhookUrl, text },
      headers: { 'Authorization': `Bearer ${API_KEY}` }
    }
  );
  return response.data;
}

// Example
postToDiscord(
  'https://discord.com/api/webhooks/123/abc',
  '🚀 New launch announcement!'
)
  .then(result => console.log(result))
  .catch(console.error);
```

---

### TypeScript

```typescript
interface PostRequest {
  text: string;
  platforms: string[];
  mediaUrls?: string[];
  subreddit?: string;
  title?: string;
  channel_id?: string;
  webhooks?: string[];
}

interface PostResponse {
  success: boolean;
  platform: string;
  post_id?: string;
  url?: string;
  error?: string;
}

class LaunchAPI {
  private apiUrl: string;
  private apiKey: string;

  constructor(apiUrl: string = 'http://localhost:8000', apiKey: string = 'dev_key') {
    this.apiUrl = apiUrl;
    this.apiKey = apiKey;
  }

  async post(request: PostRequest): Promise<PostResponse[]> {
    const response = await fetch(`${this.apiUrl}/post`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return response.json();
  }

  async healthCheck(): Promise<boolean> {
    const response = await fetch(`${this.apiUrl}/health`);
    const data = await response.json();
    return data.status === 'healthy';
  }
}

// Example usage
const api = new LaunchAPI();

async function launch() {
  const isHealthy = await api.healthCheck();
  if (!isHealthy) {
    throw new Error('API is not healthy');
  }

  const results = await api.post({
    text: '🚀 Launching today!',
    platforms: ['twitter', 'linkedin', 'reddit'],
    subreddit: 'SaaS',
    title: 'My product launch'
  });

  results.forEach(post => {
    console.log(`${post.success ? '✅' : '❌'} ${post.platform}`);
  });
}

launch();
```

---

## Retry Logic

The Launch API includes built-in retry logic with exponential backoff for handling transient failures.

### Retry Configuration

```python
from lib.retry import RetryConfig, retry_async

# Default configuration
DEFAULT_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True
)

# Aggressive (more retries, longer delays)
AGGRESSIVE_RETRY_CONFIG = RetryConfig(
    max_retries=5,
    base_delay=2.0,
    max_delay=120.0,
    exponential_base=2.0,
    jitter=True
)

# Conservative (fewer retries, shorter delays)
CONSERVATIVE_RETRY_CONFIG = RetryConfig(
    max_retries=2,
    base_delay=0.5,
    max_delay=10.0,
    exponential_base=2.0,
    jitter=True
)
```

### Retryable Errors

The retry logic automatically retries on:
- Timeout errors
- Connection errors
- Network errors
- Rate limit (429) responses
- Server errors (500, 502, 503, 504)

### Using Retry in Your Code

```python
from lib.retry import retry_async, RetryConfig

async def post_with_retry(text, platforms):
    """Post with automatic retry on failure"""
    result = await retry_async(
        post_to_platforms,
        text,
        platforms,
        config=RetryConfig(max_retries=3),
        platform="multi"
    )
    
    if result.success:
        return result.result
    else:
        print(f"Failed after {result.attempts} attempts: {result.error}")
        return None
```

---

## Best Practices

### 1. Stagger Reddit Posts

Reddit requires delays between posts to different subreddits:

```python
import time

subreddits = ["SaaS", "SideProject", "startups"]
for subreddit in subreddits:
    post_to_reddit(subreddit, title, text)
    time.sleep(600)  # Wait 10 minutes
```

### 2. Handle Errors Gracefully

```python
result = post_to_platforms(text, platforms)

for post in result:
    if not post["success"]:
        log_error(f"Failed on {post['platform']}: {post['error']}")
        # Queue for retry or manual posting
        add_to_dead_letter_queue(post)
```

### 3. Use Dry-Run Mode for Testing

```bash
python launch-hybrid.py --dry-run
```

### 4. Validate Before Posting

```python
def validate_post(text, platforms):
    if len(text) > 280 and "twitter" in platforms:
        print("Warning: Text exceeds Twitter limit")
    if "reddit" in platforms and not all([subreddit, title]):
        raise ValueError("Reddit requires subreddit and title")
```

### 5. Log All Activity

```python
import logging

logging.basicConfig(
    filename='logs/launch.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info(f"Posting to {platforms}")
```

### 6. Keep Secrets Secure

Never commit `.env` file. Use environment variables:

```bash
# .gitignore
.env
*.env.local
```

### 7. Test Individual Platforms

Before a full launch, test each platform:

```bash
# Test Twitter only
python launch-hybrid.py --platform twitter --dry-run

# Test Reddit only
python launch-hybrid.py --platform reddit --dry-run
```

---

## Additional Resources

- [README.md](./README.md) - Setup and configuration guide
- [PRD](~/Vault/Research/App Launch Strategies/PRD-launch-automation.md) - Product requirements
- [Late.dev Documentation](https://getlate.dev/docs)
- [Reddit API (PRAW)](https://praw.readthedocs.io/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Discord Webhooks](https://discord.com/developers/docs/resources/webhook)
- [Slack Webhooks](https://api.slack.com/messaging/webhooks)

---

## Support

For issues or questions:
1. Check the [Troubleshooting](./README.md#troubleshooting) section in README
2. Review server logs: `tail -f logs/launch.log`
3. Test with dry-run mode: `python launch-hybrid.py --dry-run`

---

**Last Updated:** 2026-03-08  
**API Version:** 1.0.0
