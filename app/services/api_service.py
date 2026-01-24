
import json
import base64
import requests
import mimetypes
import os

class LabsApiService:
    def __init__(self):
        self.cookies = []
        self.auth_token = ""
        self.session = requests.Session()
        
        # Standard headers from the user example
        self.base_headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "text/plain;charset=UTF-8",
            "priority": "u=1, i",
            "sec-ch-ua": "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "x-browser-channel": "stable",
            "x-browser-copyright": "Copyright 2026 Google LLC. All Rights reserved.",
            "x-browser-year": "2026"
            # x-client-data is dynamic, might be optional or tied to the browser session.
        }

    def set_credentials(self, cookie_input, auth_token=None):
        """Parse cookies and optional auth token.
        cookie_input can be either a JSON string or a list of cookie dicts.
        """
        if auth_token:
            self.auth_token = auth_token.strip()
        
        # Parse Cookies - support both JSON string and list
        try:
            if isinstance(cookie_input, str):
                self.cookies = json.loads(cookie_input)
            else:
                self.cookies = cookie_input
            
            # Store raw cookies for browser service
            self.cookies_raw = self.cookies
            
            self.session.cookies.clear()
            for cookie in self.cookies:
                if 'name' in cookie and 'value' in cookie:
                    self.session.cookies.set(
                        cookie['name'], 
                        cookie['value'], 
                        domain=cookie.get('domain', ''),
                        path=cookie.get('path', '/')
                    )
        except Exception as e:
            print(f"Error parsing cookies: {e}")
            raise e

    def _get_headers(self):
        headers = self.base_headers.copy()
        if self.auth_token:
            headers['authorization'] = self.auth_token
        # Nếu không có auth_token, request sẽ tự động dùng cookie trong session
        return headers
    
    def fetch_recaptcha_token(self, project_id=None, use_visible_browser=True):
        """
        Fetches a reCAPTCHA token using browser automation.
        This is required before calling generate_video API.
        """
        from app.services.browser_service import BrowserService
        
        if not hasattr(self, 'cookies_raw') or not self.cookies_raw:
            raise ValueError("Cookies not set. Call set_credentials first.")
        
        browser_service = BrowserService()
        
        if project_id:
            print(f"[API] Fetching reCAPTCHA token for project: {project_id}")
            token = browser_service.fetch_recaptcha_token_with_project(
                self.cookies_raw, 
                project_id, 
                use_visible_browser=use_visible_browser
            )
        else:
            print("[API] Fetching reCAPTCHA token...")
            token = browser_service.fetch_recaptcha_token(
                self.cookies_raw, 
                use_visible_browser=use_visible_browser
            )
        
        if token:
            print(f"[API] reCAPTCHA token acquired ({len(token)} chars)")
        else:
            print("[API] Failed to get reCAPTCHA token")
        
        return token

    def upload_image(self, image_path):
        url = "https://aisandbox-pa.googleapis.com/v1:uploadUserImage"
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Detect mime type
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "image/jpeg" # Default

        # Read and Encode
        # Read and Encode
        with open(image_path, "rb") as img_file:
            raw_bytes = img_file.read()
            b64_string = base64.b64encode(raw_bytes).decode('utf-8')
            
        import time
        session_id = f";{int(time.time()*1000)}"

        payload = {
            "imageInput": {
                "rawImageBytes": b64_string,
                "mimeType": mime_type,
                "isUserUploaded": True,
                "aspectRatio": "IMAGE_ASPECT_RATIO_LANDSCAPE" 
            },
            "clientContext": {
                "sessionId": session_id,
                "tool": "ASSET_MANAGER"
            }
        }
        
        headers = self._get_headers()
        headers.update({
             "sec-ch-ua-platform": "\"Windows\"",
             "Referer": "https://labs.google/",
             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
             "sec-ch-ua": "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
             "Content-Type": "text/plain;charset=UTF-8",
             "sec-ch-ua-mobile": "?0"
        })
        
        response = self.session.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        
        data = response.json()
        
        # New response format handling
        # { "mediaGenerationId": { "mediaGenerationId": "..." }, ... }
        media_id = None
        if 'mediaGenerationId' in data:
            val = data['mediaGenerationId']
            if isinstance(val, dict):
                 media_id = val.get('mediaGenerationId')
            else:
                 media_id = val
            data['mediaId'] = media_id

        # Submit Log after success
        if media_id:
             props = [
                {"key": "TOOL_NAME", "stringValue": "PINHOLE"},
                {"key": "PINHOLE_IMAGE_ASPECT_RATIO", "stringValue": "IMAGE_ASPECT_RATIO_LANDSCAPE"},
                {"key": "PINHOLE_PROMPT_BOX_MODE", "stringValue": "IMAGE_TO_VIDEO"},
                {"key": "IS_DESKTOP"}
             ]
             self.submit_batch_log(
                 session_id, 
                 "PINHOLE_CROP_IMAGE", 
                 metadata={"mediaGenerationId": media_id}, 
                 properties=props
             )

        return data

    def generate_video(self, prompt, start_image_media_id, aspect_ratio="VIDEO_ASPECT_RATIO_LANDSCAPE", count=1):
        url = "https://aisandbox-pa.googleapis.com/v1/video:batchAsyncGenerateVideoStartImage"
        
    def submit_batch_log(self, session_id, event_name="VIDEOFX_CREATE_VIDEO", metadata=None, properties=None):
        url = "https://labs.google/fx/api/trpc/general.submitBatchLog"
        
        import time
        current_time_ms = int(time.time() * 1000)
        event_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
        
        # Default properties if not provided
        if properties is None:
            properties = [
                {"key": "TOOL_NAME", "stringValue": "PINHOLE"},
                {"key": "IS_DESKTOP"}
            ]
            
        # Merge metadata
        event_metadata = {"sessionId": session_id}
        if metadata:
            event_metadata.update(metadata)

        json_payload = {
            "json": {
                "appEvents": [
                    {
                        "event": event_name,
                        "eventMetadata": event_metadata,
                        "eventProperties": properties,
                        "activeExperiments": [],
                        "eventTime": event_time
                    }
                ]
            }
        }
        
        headers = {
            'accept': '*/*',
            'content-type': 'application/json',
            'origin': 'https://labs.google',
            'referer': 'https://labs.google/fx/vi/tools/flow',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'x-client-data': 'CIa2yQEIpbbJAQipncoBCNvaygEIk6HLAQiFoM0BCJKkzwEIqqbPAQjaqs8B'
        }
        
        print(f"\n[DEBUG] Calling submit_batch_log ({event_name})")
        # print(f"[DEBUG] Payload: {json.dumps(json_payload)}")

        try:
            resp = self.session.post(url, headers=headers, json=json_payload)
            print(f"[DEBUG] Log Response: {resp.status_code}")
        except Exception as e:
            print(f"[DEBUG] Log Exception: {e}")

    def create_project(self):
        # 1. Submit Log
        import time
        session_id = f";{int(time.time()*1000)}"
        
        props = [
            {"key": "TOOL_NAME", "stringValue": "PINHOLE"},
            {"key": "G1_PAYGATE_TIER", "stringValue": "PAYGATE_TIER_TWO"},
            {"key": "PINHOLE_PROMPT_BOX_MODE", "stringValue": "TEXT_TO_VIDEO"}, # Default or passed? Example says TEXT_TO_VIDEO
            {"key": "USER_AGENT", "stringValue": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"},
            {"key": "IS_DESKTOP"}
        ]
        
        self.submit_batch_log(session_id, "PINHOLE_CREATE_NEW_PROJECT", properties=props)

        # 2. Create Project
        url = "https://labs.google/fx/api/trpc/project.createProject"
        project_title = time.strftime("Jan %d - %H:%M")
        
        payload = {
            "json": {
                "projectTitle": project_title,
                "toolName": "PINHOLE"
            }
        }
        
        headers = {
            'accept': '*/*',
            'content-type': 'application/json',
            'origin': 'https://labs.google',
            'referer': 'https://labs.google/fx/vi/tools/flow',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'x-client-data': 'CIa2yQEIpbbJAQipncoBCNvaygEIk6HLAQiFoM0BCJKkzwEIqqbPAQjaqs8B'
        }
        
        print(f"\n[DEBUG] Creating Project...")
        resp = self.session.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        
        # Extract projectId
        # Structure: { "result": { "data": { "json": { "result": { "projectId": "..." } } } } }
        try:
            # Deep extraction
            res_json = data.get('result', {}).get('data', {}).get('json', {})
            # It could be directly inside json or nested in result
            project_id = res_json.get('result', {}).get('projectId')
            
            # Fallback if structure varies
            if not project_id:
                project_id = res_json.get('id')
                
            print(f"[DEBUG] Created Project ID: {project_id}")
            return project_id
        except:
            print(f"[DEBUG] Failed to parse project ID from: {data}")
            return None

    def search_project_scenes(self, project_id):
        base_url = "https://labs.google/fx/api/trpc/project.searchProjectScenes"
        # Construct input JSON
        input_data = {
            "json": {
                "projectId": project_id,
                "toolName": "PINHOLE",
                "pageSize": 10
            }
        }
        import urllib.parse
        encoded_input = urllib.parse.quote(json.dumps(input_data))
        url = f"{base_url}?input={encoded_input}"
        
        headers = {
            'accept': '*/*',
            'content-type': 'application/json',
            'origin': 'https://labs.google',
            'referer': f'https://labs.google/fx/vi/tools/flow/project/{project_id}',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'x-client-data': 'CIa2yQEIpbbJAQipncoBCNvaygEIk6HLAQiFoM0BCJKkzwEIqqbPAQjaqs8B'
        }
        
        print(f"\n[DEBUG] Calling search_project_scenes: {project_id}")
        try:
            resp = self.session.get(url, headers=headers)
            # print(f"[DEBUG] Search Scenes Code: {resp.status_code}")
        except Exception as e:
            print(f"[DEBUG] Search Scenes Error: {e}")

    def generate_video(self, prompt, start_image_media_id, aspect_ratio="VIDEO_ASPECT_RATIO_LANDSCAPE", count=1, project_id=None, recaptcha_token=None):
        # Generate dynamic sessionId
        import time
        session_id = f";{int(time.time()*1000)}"
        current_project_id = project_id if project_id else "7636a948-fa89-4449-a8a5-72c9e008d268"

        # 0. Search Project Scenes (Pre-check)
        self.search_project_scenes(current_project_id)

        # Generate cache ID for this video generation
        cache_id = f"PINHOLE_MAIN_VIDEO_GENERATION_CACHE_ID{self._generate_guid()}"

        # 1. Log: VIDEOFX_CREATE_VIDEO (first call - matches curl)
        props_create_video = [
            {"key": "TOOL_NAME", "stringValue": "PINHOLE"},
            {"key": "QUERY_ID", "stringValue": cache_id},
            {"key": "PINHOLE_VIDEO_ASPECT_RATIO", "stringValue": aspect_ratio},
            {"key": "G1_PAYGATE_TIER", "stringValue": "PAYGATE_TIER_TWO"},
            {"key": "PINHOLE_PROMPT_BOX_MODE", "stringValue": "IMAGE_TO_VIDEO"},
            {"key": "USER_AGENT", "stringValue": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"},
            {"key": "IS_DESKTOP"}
        ]
        self.submit_batch_log(session_id, "VIDEOFX_CREATE_VIDEO", properties=props_create_video)

        # 2. Log: VIDEO_CREATION_TO_VIDEO_COMPLETION (timer event)
        # Generate a timer ID based on the cache_id guid
        timer_guid = cache_id.replace("PINHOLE_MAIN_VIDEO_GENERATION_CACHE_ID", "")
        timer_id = f"VIDEO_CREATION_TO_VIDEO_COMPLETION{timer_guid}"
        props_timer = [
            {"key": "TIMER_ID", "stringValue": timer_id},
            {"key": "TOOL_NAME", "stringValue": "PINHOLE"},
            {"key": "CURRENT_TIME_MS", "intValue": f"{int(time.time()*1000)}"},
            {"key": "USER_AGENT", "stringValue": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"},
            {"key": "IS_DESKTOP"}
        ]
        self.submit_batch_log(session_id, "VIDEO_CREATION_TO_VIDEO_COMPLETION", properties=props_timer)

        url = "https://aisandbox-pa.googleapis.com/v1/video:batchAsyncGenerateVideoStartImage"
        
        # 'requests' list based on count
        requests_list = []
        import random
        
        for _ in range(count):
            seed = random.randint(10000, 99999)
            
            # Determine Model Key based on Aspect Ratio
            # veo_3_1_i2v_s_fast_ultra (Landscape/Default?)
            # veo_3_1_i2v_s_fast_portrait_ultra
            # veo_3_1_i2v_s_fast_square_ultra (Guessing)
            
            model_key = "veo_3_1_i2v_s_fast_ultra"
            if aspect_ratio == "VIDEO_ASPECT_RATIO_PORTRAIT":
                model_key = "veo_3_1_i2v_s_fast_portrait_ultra"
            elif aspect_ratio == "VIDEO_ASPECT_RATIO_SQUARE":
                model_key = "veo_3_1_i2v_s_fast_square_ultra"

            req_item = {
                "aspectRatio": aspect_ratio,
                "seed": seed,
                "textInput": {
                    "prompt": prompt
                },
                "videoModelKey": model_key,
                "startImage": {
                    "mediaId": start_image_media_id
                },
                "metadata": {
                    "sceneId": self._generate_guid() 
                }
            }
            requests_list.append(req_item)
            
        payload = {
            "clientContext": {
                "sessionId": session_id,
                "projectId": current_project_id,
                "tool": "PINHOLE",
                "userPaygateTier": "PAYGATE_TIER_TWO"
            },
            "requests": requests_list
        }
        
        if recaptcha_token:
            payload["clientContext"]["recaptchaContext"] = {
                "token": recaptcha_token,
                "applicationType": "RECAPTCHA_APPLICATION_TYPE_WEB"
            }
        
        headers = self._get_headers()
        headers.update({
             "sec-ch-ua-platform": "\"Windows\"",
             "Referer": "https://labs.google/",
             "Origin": "https://labs.google",
             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
             "sec-ch-ua": "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
             "Content-Type": "text/plain;charset=UTF-8",
             "x-browser-channel": "stable",
             "x-browser-copyright": "Copyright 2026 Google LLC. All Rights reserved.",
             "x-browser-validation": "PHzxKQDW1JU+MpcuUrBanuCqlLI=",
             "x-browser-year": "2026",
             "x-client-data": "CIa2yQEIpbbJAQipncoBCNvaygEIk6HLAQiFoM0BCJKkzwEIqqbPAQjaqs8B"
        })
        
        print(f"\n[DEBUG] Calling generate_video used ProjectID: {payload['clientContext']['projectId']}")
        # print(f"[DEBUG] URL: {url}")
        # print(f"[DEBUG] Headers Keys: {list(headers.keys())}")
        
        response = self.session.post(url, headers=headers, json=payload)
        
        print(f"[DEBUG] Generate Response Status: {response.status_code}")
        if response.status_code >= 400:
             print(f"[DEBUG] Generate Error Body: {response.text}")
             if "reCAPTCHA" in response.text:
                 raise Exception("Google yêu cầu Recaptcha! Hiện tại API không thể bypass.\nVui lòng mở 'Browser' từ danh sách tài khoản để tạo thủ công.")

        response.raise_for_status()
        return response.json()

    def generate_video_text(self, prompt, aspect_ratio="VIDEO_ASPECT_RATIO_LANDSCAPE", count=1, project_id=None, recaptcha_token=None):
        """Generate video from Text only (Text-to-Video)"""
        import time
        import random
        
        session_id = f";{int(time.time()*1000)}"
        current_project_id = project_id if project_id else "7636a948-fa89-4449-a8a5-72c9e008d268"

        # 0. Search Project Scenes (Pre-check)
        self.search_project_scenes(current_project_id)

        # Generate cache ID
        cache_id = f"PINHOLE_MAIN_VIDEO_GENERATION"
        
        # 1. Log VIDEOFX_CREATE_VIDEO
        self.submit_batch_log(session_id, "VIDEOFX_CREATE_VIDEO")
        
        # 2. Log API latency start
        timer_id = str(random.randint(100000, 999999))
        props_timer = [
            {"key": "TIMER_ID", "stringValue": timer_id},
            {"key": "TOOL_NAME", "stringValue": "PINHOLE"},
            {"key": "CURRENT_TIME_MS", "intValue": f"{int(time.time()*1000)}"},
            {"key": "USER_AGENT", "stringValue": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"},
            {"key": "IS_DESKTOP"}
        ]
        self.submit_batch_log(session_id, "VIDEO_CREATION_TO_VIDEO_COMPLETION", properties=props_timer)

        url = "https://aisandbox-pa.googleapis.com/v1/video:batchAsyncGenerateVideoText"
        
        requests_list = []
        for _ in range(count):
            seed = random.randint(10000, 99999)
            
            # Text-to-Video Models:
            # veo_3_1_t2v_fast_ultra (Landscape)
            # veo_3_1_t2v_fast_portrait_ultra (Portrait)
            
            model_key = "veo_3_1_t2v_fast_ultra"
            if aspect_ratio == "VIDEO_ASPECT_RATIO_PORTRAIT":
                model_key = "veo_3_1_t2v_fast_portrait_ultra"

            req_item = {
                "aspectRatio": aspect_ratio,
                "seed": seed,
                "textInput": {
                    "prompt": prompt
                },
                "videoModelKey": model_key,
                "metadata": {
                    "sceneId": self._generate_guid() 
                }
            }
            requests_list.append(req_item)
            
        payload = {
            "clientContext": {
                "recaptchaContext": {
                    "token": recaptcha_token,
                    "applicationType": "RECAPTCHA_APPLICATION_TYPE_WEB"
                },
                "sessionId": session_id,
                "projectId": current_project_id,
                "tool": "PINHOLE",
                "userPaygateTier": "PAYGATE_TIER_TWO"
            },
            "requests": requests_list
        }
        
        headers = self._get_headers()
        headers.update({
             "sec-ch-ua-platform": "\"Windows\"",
             "Referer": "https://labs.google/",
             "Origin": "https://labs.google",
             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
             "sec-ch-ua": "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
             "Content-Type": "text/plain;charset=UTF-8",
             "x-browser-channel": "stable",
             "x-browser-copyright": "Copyright 2026 Google LLC. All Rights reserved.",
             "x-browser-validation": "PHzxKQDW1JU+MpcuUrBanuCqlLI=",
             "x-browser-year": "2026",
             "x-client-data": "CIa2yQEIpbbJAQipncoBCNvaygEIk6HLAQiFoM0BCJKkzwEIqqbPAQjaqs8B"
        })
        
        print(f"\n[DEBUG] Calling generate_video_text used ProjectID: {payload['clientContext']['projectId']}")
        
        response = self.session.post(url, headers=headers, json=payload)
        
        print(f"[DEBUG] Generate Response Status: {response.status_code}")
        if response.status_code >= 400:
             print(f"[DEBUG] Generate Error Body: {response.text}")
             if "reCAPTCHA" in response.text:
                 raise Exception("Recaptcha error in Text-to-Video")

        response.raise_for_status()
        return response.json()

        return response.json()

    def fetch_user_history(self):
        url = "https://labs.google/fx/api/trpc/media.fetchUserHistoryDirectly"
        # Simplified input param
        params = {
            "input": '{"json":{"type":"ASSET_MANAGER","pageSize":18,"responseScope":"RESPONSE_SCOPE_UNSPECIFIED"}}'
        }
        
        headers = self._get_headers()
        try:
            self.session.get(url, params=params, headers=headers)
        except:
            pass # Ignore history fetch errors

    def prepare_image_generation(self):
        import time
        session_id = f";{int(time.time()*1000)}"
        
        # 1. Log PINHOLE_GENERATE_IMAGE
        props = [
            {"key": "TOOL_NAME", "stringValue": "PINHOLE"},
            {"key": "G1_PAYGATE_TIER", "stringValue": "PAYGATE_TIER_TWO"},
            {"key": "PINHOLE_PROMPT_BOX_MODE", "stringValue": "IMAGE_GENERATION"},
            {"key": "USER_AGENT", "stringValue": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"},
            {"key": "IS_DESKTOP"}
        ]
        self.submit_batch_log(session_id, "PINHOLE_GENERATE_IMAGE", properties=props)
        
        # 2. History
        self.fetch_user_history()
        
        return session_id

    def generate_image_batch(self, prompt, aspect_ratio="IMAGE_ASPECT_RATIO_LANDSCAPE", count=1, project_id=None, recaptcha_token=None, image_media_id=None, session_id=None):
        """Generate images (Text-to-Image or Image-to-Image)"""
        import time
        import random
        
        if not session_id:
            session_id = f";{int(time.time()*1000)}"
            
        current_project_id = project_id if project_id else "5a3a7747-a3fd-4faa-a722-68957fd476a7"

        url = f"https://aisandbox-pa.googleapis.com/v1/projects/{current_project_id}/flowMedia:batchGenerateImages"
        
        requests_list = []
        for _ in range(count):
            seed = random.randint(100000, 999999)
            
            req_item = {
                "clientContext": {
                    "recaptchaContext": {
                        "token": recaptcha_token,
                        "applicationType": "RECAPTCHA_APPLICATION_TYPE_WEB"
                    },
                    "sessionId": session_id,
                    "projectId": current_project_id,
                    "tool": "PINHOLE" 
                },
                "seed": seed,
                "imageModelName": "GEM_PIX_2",
                "imageAspectRatio": aspect_ratio,
                "prompt": prompt,
                "imageInputs": []
            }
            
            if image_media_id:
                req_item["imageInputs"].append({
                    "name": image_media_id,
                    "imageInputType": "IMAGE_INPUT_TYPE_REFERENCE"
                })
                
            requests_list.append(req_item)
            
        payload = {
            "clientContext": {
                "recaptchaContext": {
                    "token": recaptcha_token,
                    "applicationType": "RECAPTCHA_APPLICATION_TYPE_WEB"
                },
                "sessionId": session_id,
                "projectId": current_project_id,
                "tool": "PINHOLE"
            },
            "requests": requests_list
        }
        
        headers = self._get_headers()
        headers.update({
             "sec-ch-ua-platform": "\"Windows\"",
             "Referer": "https://labs.google/",
             "Origin": "https://labs.google",
             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
             "sec-ch-ua": "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
             "Content-Type": "text/plain;charset=UTF-8",
             "x-browser-channel": "stable",
             "x-browser-copyright": "Copyright 2026 Google LLC. All Rights reserved.",
             "x-browser-validation": "PHzxKQDW1JU+MpcuUrBanuCqlLI=",
             "x-browser-year": "2026",
             "x-client-data": "CIa2yQEIpbbJAQipncoBCNvaygEIk6HLAQiFoM0BCJKkzwEIqqbPAQjaqs8B"
        })
        
        print(f"\n[DEBUG] Calling generate_image_batch used ProjectID: {current_project_id}")
        
        response = self.session.post(url, headers=headers, json=payload)
        
        print(f"[DEBUG] Image Gen Response Status: {response.status_code}")
        if response.status_code >= 400:
             print(f"[DEBUG] Image Gen Error Body: {response.text}")
             if "reCAPTCHA" in response.text:
                 raise Exception("Recaptcha error in Image Gen")

        response.raise_for_status()
        return response.json()

    def check_video_status(self, operations):
        """
        Polls status for a list of operations.
        operations input: List of dicts { "operation": {"name": "..."}, "sceneId": "...", "status": "..." }
        """
        url = "https://aisandbox-pa.googleapis.com/v1/video:batchCheckAsyncVideoGenerationStatus"
        
        payload = {
            "operations": operations
        }
        
        headers = self._get_headers()
        headers.update({
             "sec-ch-ua-platform": "\"Windows\"",
             "Referer": "https://labs.google/",
             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
             "Content-Type": "text/plain;charset=UTF-8",
        })
        
        response = self.session.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    def check_cookie(self):
        """Checks if the current session cookie is valid using Credits API."""
        url = "https://aisandbox-pa.googleapis.com/v1/credits?key=AIzaSyBtrm0o5ab1c-Ec8ZuLcGt3oJAA5VWt3pY"
        
        # Headers from user CURL
        headers = self._get_headers()
        headers.update({
             "accept": "*/*",
             "origin": "https://labs.google",
             "referer": "https://labs.google/",
             "x-client-data": "CIa2yQEIpbbJAQipncoBCNvaygEIk6HLAQiFoM0BCJKkzwEIqqbPAQjaqs8B" 
        })
        # Note: x-client-data is dynamic, hardcoding might work or might not.
        # But 'origin' and 'referer' are important for CORS.

        try:
            response = self.session.get(url, headers=headers)
            
            # 401/403 usually means invalid cookie
            if response.status_code in [401, 403]:
                return False, f"Auth Failed ({response.status_code})"
                
            response.raise_for_status()
            data = response.json()
            
            # Check for credits
            if 'credits' in data:
                return True, f"Live (Credits: {data['credits']})"
            return True, "Active (Unknown Response)"
            
        except Exception as e:
            return False, str(e)

    def _generate_guid(self):
        import uuid
        return str(uuid.uuid4())

    def fetch_access_token(self):
        """Fetches the access token using the current session cookies."""
        url = "https://labs.google/fx/api/auth/session"
        headers = {
            'accept': '*/*',
            'accept-language': 'vi-VN,vi;q=0.9,en-VN;q=0.8,en;q=0.7,fr-FR;q=0.6,fr;q=0.5,en-US;q=0.4',
            'content-type': 'application/json',
            'referer': 'https://labs.google/fx/vi/tools/flow',
            'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
        }
        
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Extract accessToken - API returns "access_token" snake_case based on user sample
            token = data.get('access_token')
            if token:
                # The token in response is raw "ya29...".
                # User sample shows it raw.
                # We need to prepend Bearer when using it.
                self.auth_token = f"Bearer {token}"
                return self.auth_token
            return None
        except Exception as e:
            print(f"Fetch Token Error: {e}")
            return None

    def download_video(self, video_url, save_path):
        """
        Downloads video from URL to local path.
        Returns True if successful, False otherwise.
        """
        import os
        
        try:
            print(f"[API] Downloading video to: {save_path}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
                'Referer': 'https://labs.google/'
            }
            
            response = self.session.get(video_url, headers=headers, stream=True)
            response.raise_for_status()
            
            # Get total size for progress
            total_size = int(response.headers.get('content-length', 0))
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
            
            # Write file
            downloaded = 0
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r[API] Downloading: {percent:.1f}%", end='', flush=True)
            
            print(f"\n[API] Download complete: {save_path}")
            return True
            
        except Exception as e:
            print(f"[API] Download error: {e}")
            return False
    
    def extract_video_url(self, operation_result):
        """
        Extracts video URL from successful operation result.
        The video URL is in: operation.metadata.video.fifeUrl
        """
        try:
            # Primary path: operation.metadata.video.fifeUrl
            operation = operation_result.get('operation', {})
            metadata = operation.get('metadata', {})
            video = metadata.get('video', {})
            
            # fifeUrl is the main video URL
            fife_url = video.get('fifeUrl')
            if fife_url:
                return fife_url
            
            # servingBaseUri is for thumbnail/image
            serving_uri = video.get('servingBaseUri')
            if serving_uri:
                return serving_uri
            
            # Fallback: check generatedMediaBlob structure (older format)
            media = operation_result.get('generatedMediaBlob', {})
            lightweight = media.get('mediaLightweight', {})
            derivations = lightweight.get('derivations', [])
            
            for deriv in derivations:
                if deriv.get('derivationType') == 'DERIVATION_VIDEO':
                    return deriv.get('url')
            
            for deriv in derivations:
                url = deriv.get('url')
                if url:
                    return url
                    
            video_url = media.get('videoUri')
            if video_url:
                return video_url
                
        except Exception as e:
            print(f"[API] Error extracting video URL: {e}")
        
        return None

