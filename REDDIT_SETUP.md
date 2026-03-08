# Reddit API Setup Guide

This guide walks you through setting up Reddit API credentials for the Launch Automation system.

## Prerequisites

- A Reddit account (recommend creating a dedicated bot account)
- Access to https://www.reddit.com/prefs/apps

## Step 1: Create a Reddit App

1. Log in to your Reddit account
2. Navigate to https://www.reddit.com/prefs/apps
3. Scroll down to the "developed applications" section
4. Click **"create another app..."** or **"create an app"**
5. Fill in the application form:
   - **name**: `launch-automation` (or any name you prefer)
   - **App type**: Select **"script"** (this is critical!)
   - **description**: Optional - e.g., "Launch automation bot"
   - **about url**: Optional - can be left blank
   - **redirect uri**: `http://localhost:8080` (required field, but not used for script apps)
6. Click **"create app"**

## Step 2: Get Your Credentials

After creating the app, you'll see your app details:

```
┌─────────────────────────────────────────┐
│ launch-automation                       │
│ p-jcoWKByJ...  ← This is CLIENT_ID     │
│ personal use script                     │
│                                         │
│ secret: kJ8f2...  ← This is SECRET     │
└─────────────────────────────────────────┘
```

- **CLIENT_ID**: The string directly under the app name (e.g., `p-jcoWKByJ...`)
- **CLIENT_SECRET**: The string next to "secret" (e.g., `kJ8f2...`)

## Step 3: Configure Environment Variables

Add the following to your `~/launch-api/.env` file:

```bash
# Reddit API Configuration
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=LaunchBot/1.0 by your_reddit_username
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
```

### Important Notes:

- **USER_AGENT**: Must follow Reddit's format guidelines. Use format: `AppName/Version by Username`
- **PASSWORD**: Required for script-type apps to authenticate via OAuth
- **2FA**: If your account has 2FA enabled, you'll need to disable it for script apps

## Step 4: Test Your Configuration

Run the setup helper to verify your configuration:

```bash
cd ~/launch-api
python reddit_setup.py --test
```

Expected output:
```
Testing Reddit configuration...

✅ REDDIT_CLIENT_ID: your_client_id
✅ REDDIT_CLIENT_SECRET: ********
✅ REDDIT_USER_AGENT: LaunchBot/1.0 by username
✅ REDDIT_USERNAME: your_username
✅ REDDIT_PASSWORD: ********

✅ All Reddit environment variables are set
✅ PRAW library installed

Testing Reddit connection...
✅ Authenticated as: your_username

Testing read access to r/test...
✅ Can access r/test (1,234,567 subscribers)
```

## Step 5: Test Posting to r/test

The `r/test` subreddit is designed for bot testing. To verify posting works:

```bash
python reddit_setup.py --test
# When prompted, type 'y' to test posting
```

Or directly:

```bash
python reddit_setup.py --post-test
```

## API Usage

### Via the Launch API

```bash
curl -X POST http://localhost:8000/reddit \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "subreddit": "test",
    "title": "My Launch Post",
    "text": "Check out my new product!"
  }'
```

### Via Multi-Platform Endpoint

```bash
curl -X POST http://localhost:8000/post \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Launching today!",
    "platforms": ["reddit"],
    "subreddit": "SaaS",
    "title": "I built a tool to solve X"
  }'
```

## Rate Limits

Reddit enforces rate limits to prevent spam:

| Action | Limit |
|--------|-------|
| Posts per subreddit | ~1 per 5 minutes |
| Comments | ~1 per minute |
| API requests | 60 per minute |

The Launch API automatically handles rate limiting when posting to multiple subreddits.

## Recommended Subreddits for Launches

| Subreddit | Best For | Requirements |
|-----------|----------|--------------|
| r/test | Testing | None |
| r/SaaS | SaaS products | 500+ karma |
| r/SideProject | Side projects | None |
| r/startups | Startups | None |
| r/Entrepreneur | Business | Account age |
| r/ProductHunters | Product Hunt | None |

## Troubleshooting

### "Invalid grant" error
- Verify username and password are correct
- Check if 2FA is enabled (not supported for script apps)

### "Rate limit exceeded" error
- Wait before posting again
- Reddit limits: ~1 post per 5 minutes per subreddit

### "PRAW not installed" error
```bash
pip install praw
```

### "Client ID not found" error
- Verify the app type is "script", not "web app"
- Recreate the app if necessary

### 403 Forbidden
- Your account may be too new
- You may not meet karma requirements for the subreddit

## Security Best Practices

1. **Use a dedicated Reddit account** for automation
2. **Never commit .env files** to version control
3. **Rotate credentials** if they're ever exposed
4. **Use environment variables** for all sensitive data
5. **Monitor your bot's activity** via Reddit's inbox

## Additional Resources

- [Reddit API Documentation](https://www.reddit.com/dev/api/)
- [PRAW Documentation](https://praw.readthedocs.io/)
- [Reddit App Preferences](https://www.reddit.com/prefs/apps)
- [Reddit Rate Limits](https://www.reddit.com/wiki/api)
