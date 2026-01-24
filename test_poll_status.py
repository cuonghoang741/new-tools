"""
Test script to check video status and see full response format.
Run this with an existing operation ID from a previous generate call.
"""

import json
import sys
sys.path.insert(0, '.')

from app.services.api_service import LabsApiService
import time

def main():
    # Load accounts from accounts.json
    try:
        with open('accounts.json', 'r', encoding='utf-8') as f:
            accounts = json.load(f)
    except FileNotFoundError:
        print("ERROR: accounts.json not found!")
        return
    
    if not accounts:
        print("ERROR: No accounts in accounts.json!")
        return
    
    # Use first account
    account = accounts[0]
    cookies = account.get('cookies', [])
    access_token = account.get('access_token', '')
    
    # Initialize API service
    api_service = LabsApiService()
    api_service.set_credentials(cookies, access_token)
    
    # Load last generate response if exists
    try:
        with open('test_generate_response.json', 'r', encoding='utf-8') as f:
            gen_response = json.load(f)
            operations = gen_response.get('operations', [])
    except FileNotFoundError:
        print("No test_generate_response.json found.")
        print("Run test_full_flow.py first to generate a video.")
        return
    
    if not operations:
        print("No operations found in response.")
        return
    
    print(f"Found {len(operations)} operations to check")
    print()
    
    # Poll status
    max_attempts = 60  # 5 minutes max
    for attempt in range(max_attempts):
        print(f"\n--- Check #{attempt + 1} ---")
        
        status_res = api_service.check_video_status(operations)
        
        # Save full response for debugging
        with open('test_status_response.json', 'w', encoding='utf-8') as f:
            json.dump(status_res, f, indent=2, ensure_ascii=False)
        
        ops = status_res.get('operations', [])
        
        pending = 0
        success = 0
        failed = 0
        
        for op in ops:
            st = op.get('status')
            op_name = op.get('operation', {}).get('name', 'unknown')
            
            if st == 'MEDIA_GENERATION_STATUS_SUCCESSFUL':
                success += 1
                print(f"  [SUCCESS] {op_name}")
                
                # Try to extract video URL
                video_url = api_service.extract_video_url(op)
                if video_url:
                    print(f"    Video URL: {video_url[:80]}...")
                else:
                    print(f"    No video URL found in structure")
                    print(f"    Full op keys: {list(op.keys())}")
                    
            elif st == 'MEDIA_GENERATION_STATUS_FAILED':
                failed += 1
                print(f"  [FAILED] {op_name}")
            else:
                pending += 1
                print(f"  [PENDING: {st}] {op_name}")
        
        print(f"\nSummary: {success} Success, {pending} Pending, {failed} Failed")
        
        if pending == 0:
            print("\nAll operations completed!")
            credits = status_res.get('remainingCredits')
            if credits:
                print(f"Remaining credits: {credits}")
            break
        
        # Update operations for next check
        operations = ops
        
        print("Waiting 5 seconds...")
        time.sleep(5)
    
    print("\n\nFull status response saved to: test_status_response.json")

if __name__ == "__main__":
    main()
