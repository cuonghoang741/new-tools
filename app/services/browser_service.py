
import json
import time
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class BrowserService:
    def __init__(self):
        self._drivers = {} # account_id -> driver
        self._lock = threading.Lock()

    def close_all_sessions(self):
        """Closes all active browser sessions."""
        # Create a copy of keys to iterate safely
        with self._lock:
            ids = list(self._drivers.keys())
            
        for account_id in ids:
            self.quit_session(account_id)

    def quit_session(self, account_id):
        """Closes a specific session."""
        driver = None
        with self._lock:
            driver = self._drivers.pop(account_id, None)
            
        if driver:
            try:
                print(f"[Browser] Closing browser session for {account_id}...")
                driver.quit()
            except Exception as e:
                print(f"[Browser] Error closing session {account_id}: {e}")
                try:
                    # Force kill if needed (Windows specific)
                    import psutil
                    proc = psutil.Process(driver.service.process.pid)
                    for child in proc.children(recursive=True):
                        child.kill()
                    proc.kill()
                except: pass

    def launch_browser(self, json_data, detach=True):
        """Standard browser launch (not for background tasks)"""
        if not json_data:
            raise ValueError("Empty JSON data")
        try:
            cookies = json.loads(json_data) if isinstance(json_data, str) else json_data
        except:
            raise ValueError("Invalid JSON")

        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        if detach:
            chrome_options.add_experimental_option("detach", True)

        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        
        try:
            driver.get("https://labs.google/fx/vi/tools/flow/")
            driver.delete_all_cookies()
            for cookie in cookies:
                try:
                    c = self._clean_cookie(cookie)
                    driver.add_cookie(c)
                except: pass
            driver.refresh()
        except: pass
        return driver

    def _clean_cookie(self, cookie):
        new_cookie = {}
        if 'name' in cookie: new_cookie['name'] = cookie['name']
        if 'value' in cookie: new_cookie['value'] = cookie['value']
        if 'domain' in cookie: new_cookie['domain'] = cookie['domain']
        if 'path' in cookie: new_cookie['path'] = cookie['path']
        if 'secure' in cookie: new_cookie['secure'] = cookie['secure']
        if 'httpOnly' in cookie: new_cookie['httpOnly'] = cookie['httpOnly']
        if 'expirationDate' in cookie: new_cookie['expiry'] = int(cookie['expirationDate'])
        elif 'expiry' in cookie: new_cookie['expiry'] = int(cookie['expiry'])
        if 'sameSite' in cookie and cookie['sameSite']:
            ss = cookie['sameSite'].lower()
            if ss == 'lax': new_cookie['sameSite'] = 'Lax'
            elif ss == 'strict': new_cookie['sameSite'] = 'Strict'
            elif ss == 'none': new_cookie['sameSite'] = 'None'
        return new_cookie

    def fetch_recaptcha_token(self, json_cookies, account_id=None, use_visible_browser=True, project_id=None, action='VIDEO_GENERATION'):
        """
        Main optimized method to fetch ReCaptcha tokens.
        If account_id is provided, the browser instance is reused.
        action: 'VIDEO_GENERATION' or 'IMAGE_GENERATION'
        """
        # If no account_id, we use a temporary one or fall back to old behavior (but user wants persistent)
        # For safety with existing code calling without account_id, let's treat it as a temporary one
        
        should_quit_at_end = False
        if not account_id:
            account_id = f"temp_{time.time()}"
            should_quit_at_end = True

        try:
            driver = self._get_or_create_session(account_id, json_cookies, use_visible_browser, project_id)
            if not driver:
                return None

            # Execute Script
            print(f"[Browser][{account_id}] Requesting token for {action}...")
            token = self._execute_token_script(driver, action)
            
            if token:
                print(f"[Browser][{account_id}] Token Acquired!")
                return token
            return None
            
        except Exception as e:
            print(f"[Browser][{account_id}] Error in fetch_recaptcha_token: {e}")
            self.quit_session(account_id)
            return None
        finally:
            if should_quit_at_end:
                self.quit_session(account_id)

    def _get_or_create_session(self, account_id, json_cookies, use_visible_browser, project_id=None):
        with self._lock:
            driver = self._drivers.get(account_id)
            if driver:
                try:
                    # Check if alive
                    driver.title
                    # Re-navigate if project_id is different and on project page? 
                    # For now, staying on flow or specific project page is fine.
                    return driver
                except:
                    print(f"[Browser][{account_id}] Exiting dead session...")
                    self._drivers.pop(account_id, None)

            # Create New
            print(f"[Browser][{account_id}] Starting new session...")
            driver = self._init_driver(use_visible_browser)
            if not driver: return None

            # Setup cookies and page
            try:
                # Set target domain
                driver.get("https://labs.google/404")
                cookies = json.loads(json_cookies) if isinstance(json_cookies, str) else json_cookies
                driver.delete_all_cookies()
                for c in cookies:
                    try: driver.add_cookie(self._clean_cookie(c))
                    except: pass
                
                # Navigate to Flow or Project
                url = "https://labs.google/fx/vi/tools/flow"
                if project_id:
                    url += f"/project/{project_id}"
                
                print(f"[Browser][{account_id}] Navigating to {url}...")
                driver.get(url)
                time.sleep(3) # Wait for initial load
                
                self._drivers[account_id] = driver
                return driver
            except Exception as e:
                print(f"[Browser][{account_id}] Setup error: {e}")
                try: driver.quit()
                except: pass
                return None

    def _init_driver(self, use_visible_browser):
        chrome_options = Options()
        if not use_visible_browser:
            chrome_options.add_argument("--headless=new")
        
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1280,720")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--log-level=3")
        
        if use_visible_browser:
            chrome_options.add_argument("--window-position=-10000,-10000")
        
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        
        if use_visible_browser:
            try: driver.set_window_position(-10000, -10000)
            except: pass
            
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        return driver

    def _execute_token_script(self, driver, action='VIDEO_GENERATION'):
        # Wait for grecaptcha
        max_wait = 30
        for _ in range(max_wait * 2):
            try:
                ready = driver.execute_script("return typeof grecaptcha !== 'undefined' && typeof grecaptcha.enterprise !== 'undefined'")
                if ready: break
            except: pass
            time.sleep(0.5)
        
        # Execute
        try:
            res = driver.execute_async_script(f"""
                const callback = arguments[arguments.length - 1];
                grecaptcha.enterprise.ready(async () => {{
                    try {{
                        const token = await grecaptcha.enterprise.execute(
                            '6LdsFiUsAAAAAIjVDZcuLhaHiDn5nnHVXVRQGeMV', 
                            {{action: '{action}'}}
                        );
                        callback({{token: token}});
                    }} catch (e) {{
                        callback({{error: e.toString()}});
                    }}
                }});
            """)
            if isinstance(res, dict):
                return res.get('token')
            return None
        except:
            return None

    # Legacy method compatibility
    def fetch_recaptcha_token_with_project(self, json_cookies, project_id, account_id=None, use_visible_browser=True, action='VIDEO_GENERATION'):
        return self.fetch_recaptcha_token(json_cookies, account_id=account_id, use_visible_browser=use_visible_browser, project_id=project_id, action=action)
