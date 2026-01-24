
import requests
import json
import os
from datetime import datetime

class AuthService:
    def __init__(self):
        self.base_url = "https://api.animostudio.vn/api"
        self.token = None
        self.user_info = None
        self.token_file = "auth_token.json"
        
    def load_token(self):
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                    self.token = data.get('accessToken')
                    # Optional calls to verify token validity if needed
                    return True
            except: pass
        return False

    def login(self, email, password):
        print(f"[AUTH] Logging in with {email}...")
        url = f"{self.base_url}/auth/login"
        payload = {"email": email, "password": password}
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            print(f"[AUTH] Login Response Code: {response.status_code}")
            print(f"[AUTH] Login Response Body: {response.text}")
            
            data = response.json()
            
            if response.status_code in (200, 201) and data.get('statusCode') == 200:
                result = data.get('result', {})
                self.token = result.get('accessToken')
                
                # Save token
                with open(self.token_file, 'w') as f:
                    json.dump(result, f)
                    
                return True, "Login Success"
            else:
                return False, f"Login Failed: {data.get('message', 'Unknown Error')}"
        except Exception as e:
            print(f"[AUTH] Login Exception: {e}")
            return False, f"Login Error: {str(e)}"

    def get_user_info(self):
        if not self.token: 
            print("[AUTH] No token to get user info")
            return None
        
        url = f"{self.base_url}/user/me"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "*/*"
        }
        
        print("[AUTH] Fetching User Info...")
        try:
            response = requests.get(url, headers=headers)
            print(f"[AUTH] User Info Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"[AUTH] User Info Body: {data}")
                self.user_info = data.get('result', {})
                return self.user_info
            print(f"[AUTH] Get User Info Failed: {response.text}")
            return None
        except Exception as e:
            print(f"[AUTH] Get User Info Exception: {e}")
            return None

    def check_license(self):
        """Check if user has active package and not expired"""
        print("[AUTH] Checking License...")
        if not self.user_info:
            self.get_user_info()
            
        if not self.user_info: 
            print("[AUTH] User Info is None")
            return False, "Cannot fetch user info (Token expired?)"
        
        active_pkg = self.user_info.get('activePackage')
        if not active_pkg:
            print("[AUTH] No active package in user info")
            return False, "Tài khoản chưa có gói Active"
            
        status = active_pkg.get('status')
        if status != 'ACTIVE':
            print(f"[AUTH] Package Status: {status}")
            return False, f"Gói cước không Active ({status})"
            
        end_date_str = active_pkg.get('endDate')
        if not end_date_str: return False, "Invalid Package Date"
        
        try:
            end_date_str = end_date_str.replace('Z', '+00:00')
            end_date = datetime.fromisoformat(end_date_str)
            now = datetime.now(end_date.tzinfo)
            
            print(f"[AUTH] Expiry: {end_date}, Now: {now}")
            
            if now > end_date:
                return False, f"Gói cước đã hết hạn vào {end_date.strftime('%d/%m/%Y')}"
                
            return True, f"Active until {end_date.strftime('%d/%m/%Y')}"
        except Exception as e:
            print(f"[AUTH] Date Parse Error: {e}")
            return False, f"Date check error: {e}"

    def logout(self):
        self.token = None
        self.user_info = None
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
