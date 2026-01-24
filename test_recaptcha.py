"""
Test script to fetch reCAPTCHA token using visible browser.
Run this to verify the token fetching works correctly.
"""

import json
import sys
sys.path.insert(0, '.')

from app.services.browser_service import BrowserService

def main():
    # Load accounts from accounts.json
    try:
        with open('accounts.json', 'r', encoding='utf-8') as f:
            accounts = json.load(f)
    except FileNotFoundError:
        print("ERROR: accounts.json not found!")
        print("Please create accounts.json with your account cookies.")
        return
    
    if not accounts:
        print("ERROR: No accounts in accounts.json!")
        return
    
    # Use first account
    account = accounts[0]
    account_name = account.get('name', 'Unknown')
    cookies = account.get('cookies', [])  # Already a list, not JSON string
    
    print(f"=== Testing ReCAPTCHA Token Fetch ===")
    print(f"Account: {account_name}")
    print()
    
    browser_service = BrowserService()
    
    # Test 1: Fetch token with visible browser (default, anti-bot)
    print("--- Test 1: Visible Browser (Recommended) ---")
    token = browser_service.fetch_recaptcha_token(cookies, use_visible_browser=True)
    
    if token:
        print(f"\n[SUCCESS] Token length: {len(token)}")
        print(f"Token preview: {token[:100]}...")
        print(f"\nFull token saved to: test_token.txt")
        
        with open('test_token.txt', 'w', encoding='utf-8') as f:
            f.write(token)
    else:
        print("\n[FAILED] Failed to get token with visible browser")
        
        # Try headless as fallback
        print("\n--- Test 2: Headless Browser (Fallback) ---")
        token = browser_service.fetch_recaptcha_token(cookies, use_visible_browser=False)
        
        if token:
            print(f"\n[SUCCESS] Headless token length: {len(token)}")
            with open('test_token.txt', 'w', encoding='utf-8') as f:
                f.write(token)
        else:
            print("\n[FAILED] Headless also failed")

if __name__ == "__main__":
    main()
