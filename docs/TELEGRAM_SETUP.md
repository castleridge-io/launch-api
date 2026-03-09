# Telegram Bot Setup Guide

This guide walks you through setting up a Telegram bot for the Launch API.

## Prerequisites

- A Telegram account
- A Telegram channel where you want to post messages
- Admin access to the channel

## Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Start a conversation with @BotFather
3. Send the command: `/newbot`
4. Follow the prompts:
   - Enter a name for your bot (e.g., "Launch Announcement Bot")
   - Enter a username for your bot (must end in `bot`, e.g., `mylaunch_bot`)
5. **Copy the API token** that BotFather provides

Example interaction:
```
You: /newbot
BotFather: Alright, a new bot. How are we going to call it?
You: Launch Announcement Bot
BotFather: Good. Now let's choose a username for your bot.
You: mylaunch_announcement_bot
BotFather: Done! Congratulations on your new bot...
Use this token to access the HTTP API:
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
Keep your token secure...
```

## Step 2: Add Bot to Your Channel

1. Open your Telegram channel
2. Tap on the channel name at the top
3. Tap on "Administrators" (or "Subscribers" > "Add Administrator")
4. Search for your bot by username (e.g., `@mylaunch_announcement_bot`)
5. Add the bot as an administrator

## Step 3: Grant Bot Permissions

When adding the bot as admin, ensure these permissions are granted:
- ✅ **Post Messages** (required)
- ✅ **Edit Messages** (optional, for updating posts)
- ❌ Other permissions can be disabled

## Step 4: Configure Environment Variables

Add the bot token to your `.env` file:

```bash
# Edit the .env file
nano ~/launch-api/.env
```

Add/update these lines:
```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHANNEL_ID=@your_channel_name
```

### Channel ID Formats

The channel ID can be in several formats:

| Format | Example | Notes |
|--------|---------|-------|
| Public channel | `@mychannel` | Use the @username |
| Private channel | `-1001234567890` | Use the numeric ID |
| Public group | `@mygroup` | Use the @username |
| Private group | `-1001234567890` | Use the numeric ID |

To find the numeric ID:
1. Forward a message from the channel to @userinfobot
2. Or use the API: `https://api.telegram.org/bot<TOKEN>/getChat?chat_id=@channelname`

## Step 5: Verify Setup

Run the verification script:

```bash
cd ~/launch-api
python tests/test_telegram_setup.py --channel @your_channel_name
```

Expected output:
```
============================================================
  TELEGRAM BOT SETUP VERIFICATION
============================================================

============================================================
  Step 1: Check Environment Variable
============================================================
✅ TELEGRAM_BOT_TOKEN
   Found: 12345678...wxyz

============================================================
  Step 2: Verify Bot Token
============================================================
✅ Bot Token Valid
   Bot: @mylaunch_bot (Launch Announcement Bot)

============================================================
  Step 3: Check Channel Admin Status
============================================================
✅ Bot is admin in @your_channel
   Found 3 admins, bot included

============================================================
  Step 4: Test Message Posting
============================================================
✅ Send Test Message
   Message sent successfully (ID: 123)
   View: https://t.me/c/your_channel/123

============================================================
  Summary
============================================================

✅ All checks passed!

Your Telegram bot is configured and ready to use.
```

## Usage

### Via API

```bash
curl -X POST 'http://localhost:8000/telegram' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "channel_id": "@your_channel",
    "text": "Hello from Launch API!"
  }'
```

### Via Python

```python
import requests

response = requests.post(
    'http://localhost:8000/telegram',
    headers={'Authorization': 'Bearer YOUR_API_KEY'},
    params={
        'channel_id': '@your_channel',
        'text': 'Hello from Launch API!'
    }
)
print(response.json())
```

### Multi-Platform Post

```bash
curl -X POST 'http://localhost:8000/post' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Exciting news! Our product is launching!",
    "platforms": ["telegram", "twitter", "linkedin"],
    "channel_id": "@your_channel"
  }'
```

## Troubleshooting

### "Bot token not configured"
- Check that `TELEGRAM_BOT_TOKEN` is set in `.env`
- Ensure no extra spaces or quotes around the token

### "Chat not found"
- Bot is not a member of the channel
- Channel ID is incorrect
- For private channels, use the numeric ID (`-100...`)

### "Forbidden: bot is not a member of the channel"
- Add the bot to the channel first
- Make sure you're using the correct channel ID

### "Forbidden: bot can't send messages to channels"
- Bot needs to be an admin, not just a member
- Grant "Post Messages" permission

### "Bad Request: chat not found"
- Verify the channel ID format
- For public channels: use `@channelname`
- For private channels: use the numeric ID

## Security Notes

- **Never commit** your bot token to version control
- The token is already in `.gitignore` via `.env`
- If token is compromised, use @BotFather to regenerate: `/revoke`

## Additional Resources

- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [BotFather Commands](https://core.telegram.org/bots/features#botfather)
- [Channel IDs Guide](https://core.telegram.org/bots/features#channels)
