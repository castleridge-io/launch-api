#!/usr/bin/env python3
"""
Test script for Late.dev API integration
Run this after configuring your LATE_API_KEY in .env
"""

import os
import sys
import requests
from dotenv import load_dotenv


def test_late_dev_connection():
    """Test Late.dev API connection and authentication"""

    print("=" * 60)
    print("Late.dev API Connection Test")
    print("=" * 60)
    print()

    # Load environment variables
    load_dotenv()

    # Check for API key
    api_key = os.getenv("LATE_API_KEY")

    if not api_key:
        print("❌ LATE_API_KEY not found in .env")
        print()
        print("Please follow these steps:")
        print("1. Visit https://getlate.dev")
        print("2. Sign up for an account")
        print("3. Go to your dashboard")
        print("4. Copy your API key")
        print("5. Add it to ~/launch-api/.env as:")
        print("   LATE_API_KEY=your_api_key_here")
        print()
        return False

    if api_key == "your_late_api_key_here":
        print("⚠️  LATE_API_KEY is still set to placeholder value")
        print()
        print("Please update ~/launch-api/.env with your actual API key from:")
        print("https://getlate.dev/dashboard")
        print()
        return False

    print(f"✅ API Key found: {api_key[:10]}...")
    print()

    # Test API connection
    print("Testing API connection...")

    try:
        # Late.dev API endpoint for account info or health check
        # Note: Adjust this endpoint based on Late.dev's actual API documentation
        response = requests.get(
            "https://api.getlate.dev/v1/accounts",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )

        if response.status_code == 200:
            print("✅ Successfully connected to Late.dev API")
            print()

            # Try to get connected accounts
            try:
                data = response.json()
                print("Connected accounts:")
                if isinstance(data, dict) and "accounts" in data:
                    for account in data["accounts"]:
                        platform = account.get("platform", "Unknown")
                        username = account.get("username", "N/A")
                        status = account.get("status", "Unknown")
                        print(f"  - {platform}: @{username} ({status})")
                elif isinstance(data, list):
                    for account in data:
                        platform = account.get("platform", "Unknown")
                        username = account.get("username", "N/A")
                        print(f"  - {platform}: @{username}")
                else:
                    print("  (No accounts data received)")
            except Exception as e:
                print(f"  Could not parse account data: {e}")

            return True

        elif response.status_code == 401:
            print("❌ Authentication failed - invalid API key")
            print("   Please check your API key at https://getlate.dev/dashboard")
            return False

        elif response.status_code == 403:
            print("❌ Access forbidden - check your subscription status")
            return False

        else:
            print(f"❌ API returned status code: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Late.dev API")
        print("   Please check your internet connection")
        return False

    except requests.exceptions.Timeout:
        print("❌ Connection timed out")
        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_post_capability():
    """Test if we can post to social platforms"""

    print()
    print("=" * 60)
    print("Testing Post Capability (Dry Run)")
    print("=" * 60)
    print()

    load_dotenv()
    api_key = os.getenv("LATE_API_KEY")

    if not api_key or api_key == "your_late_api_key_here":
        print("⚠️  Skipping post test - API key not configured")
        return False

    # Create a test post (you would replace this with actual Late.dev API)
    print("Note: This is a simulated test. Actual posting requires:")
    print("1. Connected social accounts in Late.dev dashboard")
    print("2. Proper API endpoint based on Late.dev documentation")
    print()
    print("To connect your accounts:")
    print("1. Go to https://getlate.dev/dashboard")
    print("2. Navigate to 'Connected Accounts'")
    print("3. Connect: Twitter, LinkedIn, Facebook, Instagram")
    print()

    return True


def main():
    print()

    # Test connection
    connection_ok = test_late_dev_connection()

    # Test post capability
    if connection_ok:
        test_post_capability()

    print()
    print("=" * 60)

    if connection_ok:
        print("✅ Late.dev API is configured and working!")
        print()
        print("Next steps:")
        print("1. Connect your social accounts in Late.dev dashboard")
        print("2. Run: python test_setup.py")
        print("3. Start the API: python server.py")
        print("4. Test launch: python launch-hybrid.py --dry-run")
        return 0
    else:
        print("⚠️  Late.dev API needs configuration")
        print()
        print("Please:")
        print("1. Get your API key from https://getlate.dev")
        print("2. Add it to ~/launch-api/.env")
        print("3. Run this test again: python test_late_dev.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())
