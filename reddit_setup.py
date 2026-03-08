#!/usr/bin/env python3
"""
Reddit API Setup Helper

This script guides you through setting up Reddit API credentials
and tests the connection.

Usage:
    python reddit_setup.py           # Show setup instructions
    python reddit_setup.py --test    # Test existing configuration
"""

import os
import sys


def print_instructions():
    print("""
================================================================================
                     Reddit API Setup Instructions
================================================================================

Step 1: Create a Reddit App
----------------------------
1. Log in to your Reddit account at https://www.reddit.com
2. Go to https://www.reddit.com/prefs/apps
3. Scroll down to "developed applications"
4. Click "create another app..." or "create an app"
5. Fill in the form:
   - name: launch-automation (or any name you prefer)
   - App type: Select "script" (IMPORTANT!)
   - description: Optional
   - about url: Optional
   - redirect uri: http://localhost:8080 (required but not used for script apps)
6. Click "create app"

Step 2: Get Your Credentials
-----------------------------
After creating the app, you'll see:
- Under the app name: A string like "p-jcoWKByJ..." 
  This is your CLIENT_ID
- Next to "secret": A longer string
  This is your CLIENT_SECRET

Step 3: Add to .env File
-------------------------
Add these lines to ~/launch-api/.env:

    REDDIT_CLIENT_ID=your_client_id_here
    REDDIT_CLIENT_SECRET=your_client_secret_here
    REDDIT_USER_AGENT=LaunchBot/1.0 by your_reddit_username
    REDDIT_USERNAME=your_reddit_username
    REDDIT_PASSWORD=your_reddit_password

NOTE: Your Reddit password is required for script-type apps to authenticate.

Step 4: Test the Configuration
-------------------------------
Run: python reddit_setup.py --test

================================================================================
                          Important Notes
================================================================================

- Use a dedicated Reddit account for automation to protect your main account
- Start with r/test subreddit for testing (it's designed for bot testing)
- Reddit has rate limits: ~1 post per 5 minutes per subreddit
- Your app must be "script" type, not "web app"

For more info: https://www.reddit.com/dev/api/
================================================================================
""")


def test_reddit_config():
    """Test Reddit configuration"""
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing Reddit configuration...\n")

    required_vars = [
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USER_AGENT",
        "REDDIT_USERNAME",
        "REDDIT_PASSWORD",
    ]

    missing = []
    placeholder_values = [
        "your_reddit_app_id",
        "your_reddit_app_secret",
        "your_username",
        "your_reddit_password",
    ]

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
            print(f"❌ {var}: Not set")
        elif value in placeholder_values:
            missing.append(var)
            print(f"❌ {var}: Still has placeholder value")
        else:
            if var == "REDDIT_PASSWORD":
                print(f"✅ {var}: ********")
            else:
                print(
                    f"✅ {var}: {value[:20]}..."
                    if len(value) > 20
                    else f"✅ {var}: {value}"
                )

    if missing:
        print(f"\n❌ Missing or invalid configuration for: {', '.join(missing)}")
        print("Run: python reddit_setup.py")
        return False

    print("\n✅ All Reddit environment variables are set")

    try:
        import praw

        print("✅ PRAW library installed")
    except ImportError:
        print("❌ PRAW not installed. Run: pip install praw")
        return False

    print("\nTesting Reddit connection...")
    try:
        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT"),
            username=os.getenv("REDDIT_USERNAME"),
            password=os.getenv("REDDIT_PASSWORD"),
        )

        reddit.user.me()
        print(f"✅ Authenticated as: {reddit.user.me()}")

        print("\nTesting read access to r/test...")
        subreddit = reddit.subreddit("test")
        print(f"✅ Can access r/test ({subreddit.subscribers:,} subscribers)")

        return True

    except Exception as e:
        print(f"❌ Reddit authentication failed: {e}")
        print("\nCommon issues:")
        print("- Wrong client_id or client_secret")
        print("- App type is not 'script'")
        print("- Wrong username or password")
        print("- 2FA enabled (not supported for script apps)")
        return False


def test_post_to_r_test():
    """Test posting to r/test subreddit"""
    from dotenv import load_dotenv

    load_dotenv()

    print("\n" + "=" * 60)
    print("Testing post to r/test...")
    print("=" * 60)

    try:
        import praw

        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT"),
            username=os.getenv("REDDIT_USERNAME"),
            password=os.getenv("REDDIT_PASSWORD"),
        )

        title = "Test post from Launch Automation API"
        text = "This is a test post to verify Reddit API integration. This will be deleted."

        print(f"Posting to r/test...")
        print(f"Title: {title}")

        subreddit = reddit.subreddit("test")
        submission = subreddit.submit(title, selftext=text)

        print(f"\n✅ Post successful!")
        print(f"   URL: https://reddit.com{submission.permalink}")
        print(f"   ID: {submission.id}")

        print("\nDeleting test post...")
        submission.delete()
        print("✅ Test post deleted")

        return True

    except Exception as e:
        print(f"❌ Failed to post: {e}")
        return False


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            if test_reddit_config():
                print("\n" + "=" * 60)
                response = input("Test posting to r/test? (y/n): ").strip().lower()
                if response == "y":
                    test_post_to_r_test()
        elif sys.argv[1] == "--post-test":
            test_post_to_r_test()
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Usage: python reddit_setup.py [--test|--post-test]")
    else:
        print_instructions()


if __name__ == "__main__":
    main()
