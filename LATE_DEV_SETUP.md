# Late.dev API Setup Guide

This guide walks you through setting up Late.dev API for the Launch Automation System.

## What is Late.dev?

Late.dev is an API service that simplifies posting to social media platforms that have complex OAuth requirements:
- Twitter/X
- LinkedIn
- Facebook
- Instagram
- TikTok

Instead of implementing OAuth for each platform yourself, Late.dev handles the authentication and provides a simple API.

## Setup Steps

### Step 1: Create Late.dev Account

1. Visit https://getlate.dev
2. Click "Sign Up" or "Get Started"
3. Create an account with your email

### Step 2: Get Your API Key

1. After signing up, go to your Dashboard
2. Look for "API Keys" or "Settings"
3. Copy your API key

### Step 3: Configure Environment

Add your API key to the `.env` file:

```bash
cd ~/launch-api
nano .env
```

Update this line:
```
LATE_API_KEY=your_actual_api_key_here
```

### Step 4: Connect Social Accounts

1. In Late.dev Dashboard, go to "Connected Accounts"
2. Connect each platform you want to use:
   - **Twitter/X**: Click "Connect Twitter" and authorize
   - **LinkedIn**: Click "Connect LinkedIn" and authorize
   - **Facebook**: Click "Connect Facebook" and authorize
   - **Instagram**: Click "Connect Instagram" and authorize
   - **TikTok** (optional): Click "Connect TikTok" and authorize

### Step 5: Test the Connection

Run the test script:

```bash
cd ~/launch-api
python test_late_dev.py
```

You should see:
```
✅ API Key found: sk_live_xxx...
✅ Successfully connected to Late.dev API
Connected accounts:
  - twitter: @yourusername (active)
  - linkedin: @yourprofile (active)
  ...
```

### Step 6: Test the Full System

```bash
# Test all integrations
python test_setup.py

# Start the API server
python server.py

# Test with dry-run (no actual posts)
python launch-hybrid.py --dry-run
```

## Troubleshooting

### "LATE_API_KEY not found"
- Make sure you created the `.env` file from `.env.example`
- Verify the key is correctly copied (no extra spaces)

### "Authentication failed"
- Check that your API key is valid
- Verify your Late.dev subscription is active
- Make sure you're using the correct key (live vs test)

### "No connected accounts"
- Go to Late.dev Dashboard
- Connect at least one social account
- Wait a few minutes for the connection to sync

### API Rate Limits
- Late.dev may have rate limits depending on your plan
- Check your dashboard for usage limits
- Consider upgrading if you hit limits

## Cost

Late.dev pricing (as of 2026-03):
- **Free tier**: Limited posts per month
- **Starter**: ~$29/month
- Check https://getlate.dev/pricing for current pricing

## Alternative: Direct API Integration

If you prefer not to use Late.dev, you can:
1. Implement OAuth directly for each platform
2. Use platform-specific SDKs
3. Update the server.py to use direct APIs

However, this requires:
- Twitter API (paid, $100/month minimum)
- LinkedIn API (free but complex OAuth)
- Facebook Graph API (requires app review)
- Instagram Graph API (requires business account)

## Security Notes

- Never commit your `.env` file to git
- Rotate your API key if compromised
- Use environment variables in production
- Consider using secrets management for production

## Next Steps

After Late.dev is configured:
1. Set up Reddit (see README.md)
2. Set up Telegram (see README.md)
3. Set up Discord/Slack webhooks
4. Test the full launch sequence

## Support

- Late.dev docs: https://docs.getlate.dev
- Late.dev support: Check their dashboard
- Project issues: See project repository
