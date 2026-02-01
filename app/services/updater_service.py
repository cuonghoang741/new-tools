
import requests
import os
import sys
import subprocess
import tempfile
import threading
import re

class UpdaterService:
    """
    OTA Update Service using GitHub Releases
    """
    
    GITHUB_OWNER = "cuonghoang741"
    GITHUB_REPO = "new-tools"
    CURRENT_VERSION = "2.0.0"
    
    def __init__(self):
        self.latest_version = None
        self.download_url = None
        self.release_notes = None
        self.asset_name = None
    
    @staticmethod
    def parse_version(version_str):
        """Parse version string to tuple for comparison"""
        # Remove 'v' prefix if exists
        clean = version_str.lstrip('v').strip()
        # Extract numbers
        parts = re.findall(r'\d+', clean)
        return tuple(int(p) for p in parts) if parts else (0,)
    
    def check_for_updates(self):
        """
        Check GitHub releases for newer version.
        Returns: (has_update: bool, version: str, notes: str, error: str)
        """
        try:
            url = f"https://api.github.com/repos/{self.GITHUB_OWNER}/{self.GITHUB_REPO}/releases/latest"
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "TrustLabs-AutoUpdater"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 404:
                return False, None, None, "Chưa có release nào trên GitHub"
            
            response.raise_for_status()
            data = response.json()
            
            self.latest_version = data.get("tag_name", "").lstrip('v')
            self.release_notes = data.get("body", "Không có ghi chú")
            
            # Find .exe asset
            assets = data.get("assets", [])
            for asset in assets:
                if asset.get("name", "").endswith(".exe"):
                    self.download_url = asset.get("browser_download_url")
                    self.asset_name = asset.get("name")
                    break
            
            # Compare versions
            current = self.parse_version(self.CURRENT_VERSION)
            latest = self.parse_version(self.latest_version)
            
            has_update = latest > current
            
            print(f"[Updater] Current: {current}, Latest: {latest}, HasUpdate: {has_update}")
            
            return has_update, self.latest_version, self.release_notes, None
            
        except requests.exceptions.RequestException as e:
            return False, None, None, f"Lỗi kết nối: {str(e)}"
        except Exception as e:
            return False, None, None, f"Lỗi: {str(e)}"
    
    def download_update(self, progress_callback=None):
        """
        Download the latest release .exe file.
        Returns: (success: bool, file_path: str, error: str)
        """
        if not self.download_url:
            return False, None, "Không tìm thấy file .exe trong release"
        
        try:
            # Download to temp folder
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, self.asset_name or "TrustLabs_Update.exe")
            
            print(f"[Updater] Downloading from: {self.download_url}")
            print(f"[Updater] Saving to: {temp_path}")
            
            response = requests.get(self.download_url, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            progress_callback(percent)
            
            print(f"[Updater] Download complete: {temp_path}")
            return True, temp_path, None
            
        except Exception as e:
            return False, None, f"Lỗi download: {str(e)}"
    
    def apply_update(self, new_exe_path):
        """
        Apply the update by replacing current exe and restarting.
        This creates a batch script to:
        1. Wait for current app to close
        2. Replace the exe
        3. Restart the new version
        """
        try:
            # Get current exe path
            if getattr(sys, 'frozen', False):
                # Running as compiled exe
                current_exe = sys.executable
            else:
                # Running as script - for testing, use a dummy path
                print("[Updater] Running in dev mode - skipping actual update")
                return False, "Đang chạy ở chế độ dev. Cập nhật chỉ hoạt động với file .exe"
            
            # Create update batch script
            batch_path = os.path.join(tempfile.gettempdir(), "trust_labs_update.bat")
            
            batch_script = f'''@echo off
echo Đang cập nhật Trust Labs...
timeout /t 2 /nobreak > nul
copy /y "{new_exe_path}" "{current_exe}"
if errorlevel 1 (
    echo Lỗi cập nhật! Vui lòng thử lại.
    pause
    exit /b 1
)
echo Cập nhật thành công! Đang khởi động lại...
start "" "{current_exe}"
del "%~f0"
'''
            
            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write(batch_script)
            
            print(f"[Updater] Created update script: {batch_path}")
            
            # Run the batch script and exit current app
            subprocess.Popen(
                ['cmd', '/c', batch_path],
                creationflags=subprocess.CREATE_NO_WINDOW,
                cwd=tempfile.gettempdir()
            )
            
            return True, None
            
        except Exception as e:
            return False, f"Lỗi apply update: {str(e)}"

    def get_current_version(self):
        return self.CURRENT_VERSION
