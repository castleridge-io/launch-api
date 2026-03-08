# Launch API - Hybrid System

**You own:** Reddit, Telegram, Discord, Slack (direct API)
**Late.dev handles:** Twitter, LinkedIn, Facebook, Instagram, TikTok

## Architecture

```
┌─────────────────┐
│  launch.py      │  Your launch script
└────────┬────────┘
         │
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
│(Hard)   │    │ (Easy)       │
└────┬────┘    └──────┬───────┘
     │                │
     ▼                ▼
Twitter,LI,FB   Reddit,Telegram,
IG,TikTok       Discord,Slack
```

## Quick Start

```bash
# 1. Setup
cd ~/launch-api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
nano .env  # Add your keys

# 3. Start API server
python server.py

# 4. In another terminal, launch
source venv/bin/activate
python launch-hybrid.py --dry-run
```

## What You Control

| Platform | Method | Cost | Difficulty |
|----------|--------|------|------------|
| Reddit | Direct (PRAW) | Free | Easy (1 hour) |
| Telegram | Bot API | Free | Easy (30 min) |
| Discord | Webhooks | Free | Trivial (10 min) |
| Slack | Webhooks | Free | Trivial (10 min) |

## What Late.dev Handles

| Platform | Why Hard | Late.dev Cost |
|----------|----------|---------------|
| Twitter | Requires $100/mo API | Included |
| LinkedIn | Complex OAuth, 2-4 week approval | Included |
| TikTok | Hard to get API access | Included |
| Facebook | Graph API complexity | Included |
| Instagram | Graph API complexity | Included |

## Configuration

### 1. Late.dev (Required for Twitter/LinkedIn/Facebook/Instagram)

1. Sign up at https://getlate.dev
2. Get API key from dashboard
3. Connect your social accounts
4. Add to `.env`:
   ```
   LATE_API_KEY=your_key_here
   ```

### 2. Reddit (Optional)

**See [REDDIT_SETUP.md](REDDIT_SETUP.md) for detailed setup instructions.**

Quick setup:
1. Go to https://www.reddit.com/prefs/apps
2. Create app (script type)
3. Add to `.env`:
   ```
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_client_secret
   REDDIT_USER_AGENT=LaunchBot/1.0 by your_username
   REDDIT_USERNAME=your_username
   REDDIT_PASSWORD=your_password
   ```
4. Test: `python reddit_setup.py --test`

### 3. Telegram (Optional)

1. Message @BotFather on Telegram
2. Create bot: `/newbot`
3. Add bot to channel as admin
4. Add to `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token
   ```

### 4. Discord (Optional)

1. Go to channel settings → Integrations → Webhooks
2. Create webhook
3. Add to `~/launch-automation/config/platforms.json`:
   ```json
   {
     "discord_webhooks": [
       "https://discord.com/api/webhooks/xxx/yyy"
     ]
   }
   ```

### 5. Slack (Optional)

1. Go to https://api.slack.com/apps
2. Create app → Incoming Webhooks
3. Add to `~/launch-automation/config/platforms.json`:
   ```json
   {
     "slack_webhooks": [
       "https://hooks.slack.com/services/xxx/yyy/zzz"
     ]
   }
   ```

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Post to Multiple Platforms
```bash
curl -X POST http://localhost:8000/post \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "🚀 Launching today!",
    "platforms": ["twitter", "linkedin", "reddit"],
    "subreddit": "SaaS",
    "title": "I built X to solve Y"
  }'
```

### Post to Specific Platform
```bash
# Reddit only
curl -X POST "http://localhost:8000/reddit?subreddit=SaaS&title=My%20Launch&text=Description" \
  -H "Authorization: Bearer your_api_key"

# Telegram only
curl -X POST "http://localhost:8000/telegram?channel_id=@mychannel&text=Message" \
  -H "Authorization: Bearer your_api_key"

# Discord only
curl -X POST "http://localhost:8000/discord?webhook_url=https://discord.com/...&text=Message" \
  -H "Authorization: Bearer your_api_key"
```

## Running as Service

### With systemd

```bash
# Create service file
sudo nano /etc/systemd/system/launch-api.service
```

```ini
[Unit]
Description=Launch API Server
After=network.target

[Service]
Type=simple
User=montelai
WorkingDirectory=/home/montelai/launch-api
ExecStart=/home/montelai/launch-api/venv/bin/python server.py
Restart=always
Environment=API_KEY=your_secure_key_here

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable launch-api
sudo systemctl start launch-api
```

### With Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "server.py"]
```

```bash
docker build -t launch-api .
docker run -p 8000:8000 --env-file .env launch-api
```

## Costs

| Component | Cost |
|-----------|------|
| Late.dev Free Tier | $0 (20 posts) |
| Late.dev Starter | $29/mo (500 posts) |
| Reddit API | Free |
| Telegram Bot | Free |
| Discord Webhooks | Free |
| Slack Webhooks | Free |
| Your Server | $0 (use existing) |
| **Total** | **$0-29/mo** |

## Advantages Over Full Late.dev

✅ **You own Reddit, Telegram, Discord, Slack** - no dependency
✅ **Can swap Late.dev later** if you build your own Twitter/LinkedIn integration
✅ **Full control** over easy platforms
✅ **Learn and customize** the direct integrations
✅ **Cheaper long-term** if you scale

## Disadvantages

❌ **More setup** than pure Late.dev (30 min vs 5 min)
❌ **You maintain** Reddit/Telegram code
❌ **Need server** to run API

## When to Use This vs Pure Late.dev

**Use Hybrid (this) if:**
- You want to own the integration
- You might scale beyond Late.dev limits
- You want to learn/customize
- You're technical and want control

**Use Pure Late.dev if:**
- You want fastest setup (5 min)
- You don't care about owning the integration
- You're non-technical
- You just want it to work

## Testing

```bash
# Dry run (no actual posts)
python launch-hybrid.py --dry-run

# Test specific platform
python launch-hybrid.py --platform reddit --dry-run

# Check API health
curl http://localhost:8000/health

# View logs
tail -f logs/launch.log
```

## Troubleshooting

**"Launch API not running"**
```bash
cd ~/launch-api
source venv/bin/activate
python server.py
```

**"Reddit authentication failed"**
- Verify credentials in .env
- Check Reddit app is "script" type
- Ensure username/password are correct

**"Telegram bot not authorized"**
- Add bot to channel as admin
- Use correct channel_id (with @ for public, -100... for private)

**"Late API error"**
- Verify LATE_API_KEY in .env
- Check social accounts connected in Late dashboard
- Verify Late plan has enough posts

## Next Steps

1. ✅ Install dependencies
2. ✅ Configure .env
3. ✅ Start API server
4. ✅ Test with dry run
5. ✅ Launch!
