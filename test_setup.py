#!/usr/bin/env python3
"""
Test script for Launch API
Run this to verify your setup
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required packages are installed"""
    print("Testing imports...")
    
    try:
        import fastapi
        print("✅ fastapi")
    except ImportError:
        print("❌ fastapi - run: pip install fastapi")
        return False
    
    try:
        import uvicorn
        print("✅ uvicorn")
    except ImportError:
        print("❌ uvicorn - run: pip install uvicorn")
        return False
    
    try:
        import requests
        print("✅ requests")
    except ImportError:
        print("❌ requests - run: pip install requests")
        return False
    
    try:
        import pydantic
        print("✅ pydantic")
    except ImportError:
        print("❌ pydantic - run: pip install pydantic")
        return False
    
    # Optional: Reddit
    try:
        import praw
        print("✅ praw (optional)")
    except ImportError:
        print("⚠️  praw not installed - Reddit posting disabled")
        print("   Install with: pip install praw")
    
    return True

def test_env():
    """Test .env configuration"""
    print("\nTesting .env configuration...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    # Required for Late.dev
    late_key = os.getenv("LATE_API_KEY")
    if late_key and late_key != "your_late_api_key_here":
        print("✅ LATE_API_KEY configured")
    else:
        print("⚠️  LATE_API_KEY not configured - Twitter/LinkedIn/FB/IG disabled")
        print("   Get key at: https://getlate.dev")
    
    # Optional: Reddit
    reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
    if reddit_client_id and reddit_client_id != "your_reddit_app_id":
        print("✅ Reddit configured")
    else:
        print("⚠️  Reddit not configured - Reddit posting disabled")
    
    # Optional: Telegram
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if telegram_token and telegram_token != "your_telegram_bot_token":
        print("✅ Telegram configured")
    else:
        print("⚠️  Telegram not configured - Telegram posting disabled")
    
    return True

def test_api_server():
    """Test if API server is running"""
    print("\nTesting API server...")
    
    import requests
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ API server running at http://localhost:8000")
            return True
        else:
            print("❌ API server returned error:", response.status_code)
            return False
    except requests.exceptions.ConnectionError:
        print("⚠️  API server not running")
        print("   Start with: python server.py")
        return False
    except Exception as e:
        print("❌ Error connecting to API:", str(e))
        return False

def main():
    print("=" * 50)
    print("Launch API Test Suite")
    print("=" * 50)
    print()
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Environment", test_env()))
    results.append(("API Server", test_api_server()))
    
    print()
    print("=" * 50)
    print("Test Results")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All tests passed!")
        print()
        print("You can now:")
        print("1. Start the API: python server.py")
        print("2. Test launch: python launch-hybrid.py --dry-run")
    else:
        print("⚠️  Some tests failed. Fix the issues above and re-run.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
