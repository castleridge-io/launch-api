#!/usr/bin/env python3
"""
Launch Script - Hybrid Version
Uses local Launch API (which uses Late.dev for hard platforms)
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("❌ Missing dependency: requests")
    print("   Run: pip install requests")
    sys.exit(1)

# ============================================
# CONFIGURATION
# ============================================

SCRIPT_DIR = Path(__file__).parent
CONFIG_DIR = SCRIPT_DIR.parent.parent / "launch-automation" / "config"
LOGS_DIR = SCRIPT_DIR.parent / "logs"

# Load configs
def load_config():
    platforms_path = CONFIG_DIR / "platforms.json"
    messages_path = CONFIG_DIR / "messages.json"
    
    if not platforms_path.exists():
        print(f"❌ Config not found: {platforms_path}")
        sys.exit(1)
    
    if not messages_path.exists():
        print(f"❌ Config not found: {messages_path}")
        sys.exit(1)
    
    with open(platforms_path) as f:
        platforms = json.load(f)
    
    with open(messages_path) as f:
        messages = json.load(f)
    
    return platforms, messages

# ============================================
# LOGGING
# ============================================

LOG_FILE = LOGS_DIR / "launch.log"

def log(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{level}] {message}"
    print(entry)
    
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")

# ============================================
# API CLIENT
# ============================================

class LaunchAPIClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def post(self, endpoint: str, data: dict):
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, json=data, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"API error: {response.status_code} - {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def health(self):
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

# ============================================
# POSTING FUNCTIONS
# ============================================

def post_via_api(client: LaunchAPIClient, text: str, platforms: list, media_urls: list = None, **kwargs):
    """Post to multiple platforms via Launch API"""
    payload = {
        "text": text,
        "platforms": platforms,
        "mediaUrls": media_urls or [],
        **kwargs
    }
    
    result = client.post("/post", payload)
    
    if isinstance(result, list):
        for r in result:
            if r.get("success"):
                log(f"✅ Posted to {r.get('platform')}", "SUCCESS")
            else:
                log(f"❌ Failed to post to {r.get('platform')}: {r.get('error')}", "ERROR")
    else:
        if result.get("success"):
            log(f"✅ Posted successfully", "SUCCESS")
        else:
            log(f"❌ Failed: {result.get('error')}", "ERROR")
    
    return result

def post_reddit(client: LaunchAPIClient, subreddit: str, title: str, body: str):
    """Post to Reddit via Launch API"""
    result = client.post("/reddit", {
        "subreddit": subreddit,
        "title": title,
        "text": body
    })
    
    if result.get("success"):
        log(f"✅ Posted to r/{subreddit}: {result.get('url')}", "SUCCESS")
    else:
        log(f"❌ Failed to post to r/{subreddit}: {result.get('error')}", "ERROR")
    
    return result

def post_telegram(client: LaunchAPIClient, channel_id: str, text: str):
    """Post to Telegram via Launch API"""
    result = client.post("/telegram", {
        "channel_id": channel_id,
        "text": text
    })
    
    if result.get("success"):
        log(f"✅ Posted to Telegram", "SUCCESS")
    else:
        log(f"❌ Failed to post to Telegram: {result.get('error')}", "ERROR")
    
    return result

def post_discord(client: LaunchAPIClient, webhooks: list, text: str):
    """Post to Discord via Launch API"""
    for webhook_url in webhooks:
        if "YOUR_WEBHOOK" in webhook_url:
            log("⚠️ Skipping unconfigured Discord webhook", "WARN")
            continue
        
        result = client.post("/discord", {
            "webhook_url": webhook_url,
            "text": text
        })
        
        if result.get("success"):
            log(f"✅ Posted to Discord", "SUCCESS")
        else:
            log(f"❌ Failed to post to Discord: {result.get('error')}", "ERROR")
        
        time.sleep(2)

def post_slack(client: LaunchAPIClient, webhooks: list, text: str):
    """Post to Slack via Launch API"""
    for webhook_url in webhooks:
        if "YOUR_WEBHOOK" in webhook_url:
            log("⚠️ Skipping unconfigured Slack webhook", "WARN")
            continue
        
        result = client.post("/slack", {
            "webhook_url": webhook_url,
            "text": text
        })
        
        if result.get("success"):
            log(f"✅ Posted to Slack", "SUCCESS")
        else:
            log(f"❌ Failed to post to Slack: {result.get('error')}", "ERROR")
        
        time.sleep(2)

# ============================================
# TEMPLATE SUBSTITUTION
# ============================================

def substitute_template(template: str, product: dict) -> str:
    """Replace placeholders with product info"""
    result = template
    result = result.replace("[PRODUCT_NAME]", product.get("name", ""))
    result = result.replace("[URL]", product.get("url", ""))
    result = result.replace("[Tagline]", product.get("tagline", ""))
    result = result.replace("[tagline]", product.get("tagline", ""))
    result = result.replace("[Description]", product.get("description", ""))
    return result

# ============================================
# MAIN LAUNCH FUNCTION
# ============================================

def launch(dry_run: bool = False, api_url: str = "http://localhost:8000", platform_only: str = None):
    """Execute full launch sequence"""
    
    # Load config
    config, messages = load_config()
    product = messages.get("product", {})
    
    log("=" * 60)
    log("🚀 LAUNCH SEQUENCE INITIATED (Hybrid Mode)")
    log("=" * 60)
    
    if dry_run:
        log("⚠️ DRY RUN MODE - No posts will be made", "WARN")
    
    # Initialize API client
    api_key = config.get("launch_api_key", "dev_key")
    client = LaunchAPIClient(api_url, api_key)
    
    # Check API health
    if not dry_run:
        if not client.health():
            log(f"❌ Launch API not running at {api_url}", "ERROR")
            log("   Start it with: cd ~/launch-api && python server.py", "INFO")
            return
        log(f"✅ Launch API connected: {api_url}", "SUCCESS")
    
    # ========================================
    # STEP 1: Twitter, LinkedIn, Facebook, Instagram (via Late.dev)
    # ========================================
    if not platform_only or platform_only in ["twitter", "linkedin", "facebook", "instagram"]:
        log("\n📢 Step 1: Twitter, LinkedIn, Facebook, Instagram (via Late.dev)", "INFO")
        
        # Twitter thread
        if not platform_only or platform_only == "twitter":
            twitter_messages = [substitute_template(t, product) for t in messages["twitter"]["thread"]]
            # For threads, we'd need thread support - for now just post main tweet
            if not dry_run:
                post_via_api(client, twitter_messages[0], ["twitter"])
            else:
                log(f"[DRY RUN] Would post to Twitter: {twitter_messages[0][:50]}...", "DEBUG")
        
        # LinkedIn
        if not platform_only or platform_only == "linkedin":
            linkedin_msg = substitute_template(messages["linkedin"]["main"], product)
            if not dry_run:
                post_via_api(client, linkedin_msg, ["linkedin"])
            else:
                log(f"[DRY RUN] Would post to LinkedIn", "DEBUG")
        
        # Facebook
        if not platform_only or platform_only == "facebook":
            facebook_msg = substitute_template(messages["facebook"]["main"], product)
            if not dry_run:
                post_via_api(client, facebook_msg, ["facebook"])
            else:
                log(f"[DRY RUN] Would post to Facebook", "DEBUG")
        
        # Instagram
        if not platform_only or platform_only == "instagram":
            instagram_msg = substitute_template(messages["instagram"]["caption"], product)
            if not dry_run:
                post_via_api(client, instagram_msg, ["instagram"])
            else:
                log(f"[DRY RUN] Would post to Instagram", "DEBUG")
    
    # ========================================
    # STEP 2: Reddit (direct)
    # ========================================
    if not platform_only or platform_only == "reddit":
        log("\n📢 Step 2: Reddit (direct)", "INFO")
        reddit_messages = messages.get("reddit", {})
        
        for i, (subreddit, content) in enumerate(reddit_messages.items()):
            if i > 0 and not dry_run:
                log(f"   ⏳ Waiting 5 minutes before next Reddit post...", "INFO")
                time.sleep(300)
            
            title = substitute_template(content["title"], product)
            body = substitute_template(content["body"], product)
            
            if not dry_run:
                post_reddit(client, subreddit, title, body)
            else:
                log(f"[DRY RUN] Would post to r/{subreddit}: {title}", "DEBUG")
    
    # ========================================
    # STEP 3: Telegram (direct)
    # ========================================
    if not platform_only or platform_only == "telegram":
        log("\n📢 Step 3: Telegram (direct)", "INFO")
        telegram_config = config.get("telegram", {})
        channel_id = telegram_config.get("channel_id", "")
        
        if channel_id and "YOUR_" not in channel_id:
            telegram_msg = substitute_template(messages["telegram"]["message"], product)
            if not dry_run:
                post_telegram(client, channel_id, telegram_msg)
            else:
                log(f"[DRY RUN] Would post to Telegram: {channel_id}", "DEBUG")
        else:
            log("⚠️ Telegram not configured, skipping", "WARN")
    
    # ========================================
    # STEP 4: Discord (direct)
    # ========================================
    if not platform_only or platform_only == "discord":
        log("\n📢 Step 4: Discord (direct)", "INFO")
        discord_msg = substitute_template(messages["discord"]["message"], product)
        webhooks = config.get("discord_webhooks", [])
        
        if not dry_run:
            post_discord(client, webhooks, discord_msg)
        else:
            log(f"[DRY RUN] Would post to {len(webhooks)} Discord webhooks", "DEBUG")
    
    # ========================================
    # STEP 5: Slack (direct)
    # ========================================
    if not platform_only or platform_only == "slack":
        log("\n📢 Step 5: Slack (direct)", "INFO")
        slack_msg = substitute_template(messages["slack"]["message"], product)
        webhooks = config.get("slack_webhooks", [])
        
        if not dry_run:
            post_slack(client, webhooks, slack_msg)
        else:
            log(f"[DRY RUN] Would post to {len(webhooks)} Slack webhooks", "DEBUG")
    
    # ========================================
    # COMPLETE
    # ========================================
    log("\n" + "=" * 60)
    log("🎉 LAUNCH SEQUENCE COMPLETE")
    log("=" * 60)
    
    log("\n⚠️ MANUAL STEPS REQUIRED:", "WARN")
    log("1. Product Hunt - Submit manually at 12:01 AM PT")
    log("2. Hacker News - Submit 'Show HN' manually")
    log("3. Press/PR - Send personalized emails to journalists")

# ============================================
# CLI
# ============================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Launch Script - Hybrid Mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launch-hybrid.py --dry-run              # Test without posting
  python launch-hybrid.py                         # Launch now
  python launch-hybrid.py --api-url http://localhost:8000
  python launch-hybrid.py --platform reddit     # Launch only on Reddit
        """
    )
    
    parser.add_argument("--dry-run", action="store_true", help="Test without making actual posts")
    parser.add_argument("--api-url", type=str, default="http://localhost:8000", help="Launch API URL")
    parser.add_argument("--platform", type=str, help="Launch only on specific platform")
    
    args = parser.parse_args()
    
    launch(dry_run=args.dry_run, api_url=args.api_url, platform_only=args.platform)
