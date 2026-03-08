#!/usr/bin/env python3
"""
Telegram Bot Setup Verification Script

Run this script after creating your Telegram bot to verify the configuration.

Usage:
    python tests/test_telegram_setup.py

Prerequisites:
    1. Create a bot via @BotFather on Telegram
    2. Add TELEGRAM_BOT_TOKEN to your .env file
    3. Add the bot as admin to your channel
"""

import os
import sys
import asyncio
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import requests


class TelegramSetupVerifier:
    def __init__(self):
        load_dotenv()
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.base_url = (
            f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
        )
        self.errors = []
        self.warnings = []

    def print_header(self, title: str):
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)

    def print_result(self, test_name: str, success: bool, message: str = ""):
        icon = "✅" if success else "❌"
        print(f"{icon} {test_name}")
        if message:
            print(f"   {message}")
        if not success:
            self.errors.append(f"{test_name}: {message}")

    def check_env_token(self) -> bool:
        """Check if TELEGRAM_BOT_TOKEN is set in environment"""
        self.print_header("Step 1: Check Environment Variable")

        if not self.bot_token:
            self.print_result(
                "TELEGRAM_BOT_TOKEN", False, "Token not found in .env file"
            )
            print("\n   To fix:")
            print("   1. Open ~/launch-api/.env")
            print("   2. Add: TELEGRAM_BOT_TOKEN=your_token_here")
            return False

        if self.bot_token == "your_telegram_bot_token":
            self.print_result(
                "TELEGRAM_BOT_TOKEN", False, "Token is still placeholder value"
            )
            return False

        masked_token = (
            f"{self.bot_token[:8]}...{self.bot_token[-4:]}"
            if len(self.bot_token) > 12
            else "***"
        )
        self.print_result("TELEGRAM_BOT_TOKEN", True, f"Found: {masked_token}")
        return True

    def check_bot_info(self) -> Optional[dict]:
        """Verify bot token by calling getMe API"""
        self.print_header("Step 2: Verify Bot Token")

        if not self.base_url:
            self.print_result("Bot Token Validation", False, "No token configured")
            return None

        try:
            response = requests.get(f"{self.base_url}/getMe", timeout=10)
            data = response.json()

            if data.get("ok"):
                bot_info = data.get("result", {})
                bot_name = bot_info.get("first_name", "Unknown")
                bot_username = bot_info.get("username", "Unknown")
                self.print_result(
                    "Bot Token Valid", True, f"Bot: @{bot_username} ({bot_name})"
                )
                return bot_info
            else:
                error_desc = data.get("description", "Unknown error")
                self.print_result("Bot Token Valid", False, error_desc)
                print("\n   To fix:")
                print("   1. Go to Telegram and search @BotFather")
                print("   2. Send /newbot to create a new bot")
                print("   3. Copy the token and add to .env")
                return None

        except requests.exceptions.ConnectionError:
            self.print_result("Bot Token Valid", False, "Network connection error")
            return None
        except Exception as e:
            self.print_result("Bot Token Valid", False, str(e))
            return None

    def check_bot_admin_status(self, channel_id: str) -> bool:
        """Check if bot is admin in the specified channel"""
        self.print_header("Step 3: Check Channel Admin Status")

        if not self.base_url:
            self.print_result("Channel Admin Check", False, "No token configured")
            return False

        try:
            response = requests.get(
                f"{self.base_url}/getChatAdministrators",
                params={"chat_id": channel_id},
                timeout=10,
            )
            data = response.json()

            if data.get("ok"):
                admins = data.get("result", [])
                bot_username = None

                bot_info_response = requests.get(f"{self.base_url}/getMe", timeout=10)
                if bot_info_response.json().get("ok"):
                    bot_username = (
                        bot_info_response.json().get("result", {}).get("username")
                    )

                is_admin = any(
                    admin.get("user", {}).get("username") == bot_username
                    for admin in admins
                )

                if is_admin:
                    self.print_result(
                        f"Bot is admin in {channel_id}",
                        True,
                        f"Found {len(admins)} admins, bot included",
                    )
                    return True
                else:
                    self.print_result(
                        f"Bot is admin in {channel_id}",
                        False,
                        "Bot is not in admin list",
                    )
                    print("\n   To fix:")
                    print("   1. Open your channel in Telegram")
                    print("   2. Go to Channel Info > Administrators")
                    print("   3. Add your bot as administrator")
                    print("   4. Grant 'Post Messages' permission")
                    return False
            else:
                error_desc = data.get("description", "Unknown error")
                if "chat not found" in error_desc.lower():
                    self.print_result(
                        f"Channel {channel_id}",
                        False,
                        "Channel not found or bot not a member",
                    )
                    print("\n   To fix:")
                    print("   1. Add the bot to your channel first")
                    print("   2. Then promote it to administrator")
                else:
                    self.print_result(f"Channel Admin Check", False, error_desc)
                return False

        except Exception as e:
            self.print_result("Channel Admin Check", False, str(e))
            return False

    async def test_send_message(
        self, channel_id: str, test_message: Optional[str] = None
    ) -> bool:
        """Test sending a message to the channel"""
        self.print_header("Step 4: Test Message Posting")

        if not self.bot_token:
            self.print_result("Send Test Message", False, "No token configured")
            return False

        if not test_message:
            test_message = "🤖 Test message from Launch API setup verification"

        try:
            from server import post_to_telegram

            result = await post_to_telegram(channel_id, test_message)

            if result.get("success"):
                self.print_result(
                    "Send Test Message",
                    True,
                    f"Message sent successfully (ID: {result.get('post_id')})",
                )
                if result.get("url"):
                    print(f"   View: {result['url']}")
                return True
            else:
                error = result.get("error", "Unknown error")
                self.print_result("Send Test Message", False, error)

                if "chat not found" in error.lower():
                    print("\n   This usually means:")
                    print("   1. Bot is not a member of the channel, OR")
                    print("   2. Bot is not an admin in the channel")
                elif "forbidden" in error.lower():
                    print("\n   This usually means:")
                    print("   1. Bot doesn't have permission to post")
                    print("   2. Channel ID is incorrect")
                return False

        except Exception as e:
            self.print_result("Send Test Message", False, str(e))
            return False

    def print_summary(self):
        """Print final summary"""
        self.print_header("Summary")

        if self.errors:
            print(f"\n❌ {len(self.errors)} issue(s) found:\n")
            for error in self.errors:
                print(f"   • {error}")
            print("\n📖 Full setup guide: ~/launch-api/docs/TELEGRAM_SETUP.md")
            return False
        else:
            print("\n✅ All checks passed!")
            print("\nYour Telegram bot is configured and ready to use.")
            print("\nTo post to Telegram:")
            print("   curl -X POST 'http://localhost:8000/telegram' \\")
            print("     -H 'Authorization: Bearer YOUR_API_KEY' \\")
            print("     -H 'Content-Type: application/json' \\")
            print('     -d \'{"channel_id": "@your_channel", "text": "Hello!"}\'')
            return True


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Verify Telegram bot setup")
    parser.add_argument(
        "--channel",
        "-c",
        help="Channel ID to test (e.g., @mychannel or -1001234567890)",
        default=None,
    )
    parser.add_argument(
        "--skip-post", action="store_true", help="Skip the test message posting step"
    )

    args = parser.parse_args()

    verifier = TelegramSetupVerifier()

    print("=" * 60)
    print("  TELEGRAM BOT SETUP VERIFICATION")
    print("=" * 60)

    if not verifier.check_env_token():
        verifier.print_summary()
        return 1

    bot_info = verifier.check_bot_info()
    if not bot_info:
        verifier.print_summary()
        return 1

    channel_id = args.channel or os.getenv("TELEGRAM_CHANNEL_ID")
    if channel_id:
        if not verifier.check_bot_admin_status(channel_id):
            verifier.print_summary()
            return 1

        if not args.skip_post:
            asyncio.run(verifier.test_send_message(channel_id))
    else:
        verifier.print_header("Step 3: Channel Admin Status")
        print("⚠️  No channel ID provided")
        print("   To test channel posting, run:")
        print("   python tests/test_telegram_setup.py --channel @your_channel")
        print("\n   Or set TELEGRAM_CHANNEL_ID in your .env file")
        verifier.warnings.append("Channel admin status not verified")

    success = verifier.print_summary()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
