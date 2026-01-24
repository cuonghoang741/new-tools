
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
