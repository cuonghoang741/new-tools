"""
Full test script for the complete video generation flow:
1. Load account from accounts.json
2. Upload image (if provided)
3. Fetch reCAPTCHA token via browser
4. Call generate_video API with token

Usage:
    python test_full_flow.py [image_path] [prompt]
"""

import json
import sys
sys.path.insert(0, '.')

from app.services.api_service import LabsApiService

def main():
    # Default test values
    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    prompt = sys.argv[2] if len(sys.argv) > 2 else "A gentle breeze moves through the scene"
    
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
    account_name = account.get('name', 'Unknown')
    cookies = account.get('cookies', [])
    access_token = account.get('access_token', '')
    project_id = account.get('project_id', None)
    
    print("=" * 60)
    print("GOOGLE LABS VIDEO GENERATION - FULL FLOW TEST")
    print("=" * 60)
    print(f"Account: {account_name}")
    print(f"Project ID: {project_id}")
    print(f"Prompt: {prompt}")
    print(f"Image: {image_path or 'None (will use existing media ID)'}")
    print("=" * 60)
    
    # Initialize API service
    api_service = LabsApiService()
    api_service.set_credentials(cookies, access_token)
    
    # Step 1: Upload image (if provided)
    media_id = None
    if image_path:
        print("\n[STEP 1] Uploading image...")
        try:
            result = api_service.upload_image(image_path)
            media_id = result.get('mediaId')
            print(f"  - Upload successful!")
            print(f"  - Media ID: {media_id}")
        except Exception as e:
            print(f"  - Upload failed: {e}")
            return
    else:
        # Use a test media ID if no image provided
        # You would normally get this from a previous upload
        print("\n[STEP 1] Skipping image upload (no image provided)")
        print("  - Please provide an image path as argument, or set media_id manually")
        # Example: media_id = "CAMaJGY5NzM4OTc3LTQyN2MtNGJjZS1hYzJjLTg1ZDEwOGMxOTc2ZiIDQ0FFKiRkOWQ0MGE3NC01YjMzLTQ5YzEtYTQ3ZC0xNjg4NGY5MWI3NjI"
        return
    
    # Step 2: Fetch reCAPTCHA token
    print("\n[STEP 2] Fetching reCAPTCHA token via browser...")
    try:
        recaptcha_token = api_service.fetch_recaptcha_token(
            project_id=project_id,
            use_visible_browser=True
        )
        if not recaptcha_token:
            print("  - Failed to get reCAPTCHA token!")
            return
        print(f"  - Token acquired ({len(recaptcha_token)} chars)")
    except Exception as e:
        print(f"  - Token fetch failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Generate video
    print("\n[STEP 3] Calling generate_video API...")
    try:
        result = api_service.generate_video(
            prompt=prompt,
            start_image_media_id=media_id,
            aspect_ratio="VIDEO_ASPECT_RATIO_LANDSCAPE",
            count=1,
            project_id=project_id,
            recaptcha_token=recaptcha_token
        )
        print("  - API call successful!")
        print(f"  - Response: {json.dumps(result, indent=2)[:500]}...")
        
        # Save full response
        with open('test_generate_response.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print("  - Full response saved to: test_generate_response.json")
        
    except Exception as e:
        print(f"  - Generate video failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 60)
    print("FLOW COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
