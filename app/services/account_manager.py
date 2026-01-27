
import json
import os

class AccountManager:
    def __init__(self, file_path="accounts.json"):
        self.file_path = file_path
        self.accounts = self.load_accounts()

    def load_accounts(self):
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def save_accounts(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.accounts, f, ensure_ascii=False, indent=2)

    def add_account(self, cookie_json, access_token=None, project_id=None):
        # Try to extract email or distinct name
        try:
            cookies = json.loads(cookie_json)
        except:
            raise ValueError("Invalid JSON")
        
        email = "Unknown"
        for c in cookies:
            if c.get('name') in ['email', 'EMAIL']:
                import urllib.parse
                email = urllib.parse.unquote(c.get('value', ''))
                break
        
        # Check duplicate email
        if email != "Unknown":
            for acc in self.accounts:
                existing_email = acc.get('name', '').split(' (')[0]
                if existing_email.lower() == email.lower():
                    raise ValueError(f"Tài khoản {email} đã tồn tại!")
        
        name = f"{email} ({len(self.accounts) + 1})"
        
        account = {
            "name": name,
            "cookies": cookies,
            "access_token": access_token,
            "project_id": project_id,
            "status": "Unknown"
        }
        self.accounts.append(account)
        self.save_accounts()
        return account

    def delete_account(self, index):
        if 0 <= index < len(self.accounts):
            del self.accounts[index]
            self.save_accounts()

    def get_account(self, index):
        if 0 <= index < len(self.accounts):
            return self.accounts[index]
        return None

    def check_all_live(self):
        from app.services.api_service import LabsApiService
        changed = False
        
        for acc in self.accounts:
            try:
                # Re-check status
                api = LabsApiService()
                cookies = acc.get('cookies')
                if not cookies: continue
                
                # If cookies is list, convert to json str? no, set_credentials handles list
                api.set_credentials(cookies, acc.get('access_token'))
                
                # If missing auth token, try quick fetch (silent)
                if not api.auth_token:
                    try: 
                        t = api.fetch_access_token()
                        if t: 
                            acc['access_token'] = t
                            api.auth_token = t
                            changed = True
                    except: pass

                valid, msg = api.check_cookie()
                
                new_st = "Live" if valid else "Die"
                
                # Extract credit info from msg
                # Format: "Live (Credits: 500)"
                if valid and "Credits:" in msg:
                    try:
                        credit = msg.split('Credits:')[1].strip().strip(')')
                        new_st += f" ({credit})"
                    except: pass
                
                if acc.get('status') != new_st:
                    acc['status'] = new_st
                    changed = True
            except Exception as e:
                print(f"Check failed for {acc.get('name')}: {e}")
        
        if changed: self.save_accounts()
        return changed
