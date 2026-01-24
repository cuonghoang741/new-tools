
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import tkinter as tk
from tkinter import messagebox
import time

class BrowserService:
    _drivers = {} # Cache drivers: key -> driver instance

    def launch_browser(self, json_data, detach=True):
        if not json_data:
            raise ValueError("Empty JSON data")

        try:
            cookies = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        if not isinstance(cookies, list):
            raise ValueError("JSON must be a list")

        target_domain = None
        for cookie in cookies:
            if 'domain' in cookie:
                d = cookie['domain'].lstrip('.')
                if d:
                    target_domain = d
                    break
        
        if not target_domain:
            target_domain = "labs.google" 
        
        target_url = f"https://{target_domain}/fx/vi/tools/flow/"
        
        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        if detach:
            chrome_options.add_experimental_option("detach", True)

        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        
        try:
            driver.get(target_url)
        except:
            pass
            
        driver.delete_all_cookies()
        
        for cookie in cookies:
            try:
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
                
                driver.add_cookie(new_cookie)
            except: pass
        
        driver.get(target_url)
        return driver

    def fetch_recaptcha_token(self, json_cookies, use_visible_browser=True, cache_key=None):
        import time
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        driver = None
        used_cache = False
        
        # 1. Reuse logic
        if cache_key and cache_key in self._drivers:
            driver = self._drivers[cache_key]
            try:
                driver.title 
                print(f"[Browser] Reusing cached driver for {cache_key}")
                used_cache = True
            except:
                print(f"[Browser] Cached driver {cache_key} is dead.")
                driver = None
                del self._drivers[cache_key]

        # 2. New driver logic
        if not driver:
            print("[Browser] Launching New Driver...")
            chrome_options = Options()
            if not use_visible_browser:
                chrome_options.add_argument("--headless=new")
            
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--window-size=500,600") # Small visible window
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--log-level=3")
            
            try:
                driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
                
                driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                })
                
                if cache_key:
                    self._drivers[cache_key] = driver
                
                driver.get("https://labs.google/404")
                
                if isinstance(json_cookies, str):
                    cookies = json.loads(json_cookies)
                else:
                    cookies = json_cookies
                
                driver.delete_all_cookies()
                for cookie in cookies:
                    try:
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
                        driver.add_cookie(new_cookie)
                    except: pass
                
                print("[Browser] Loading Labs Flow page...")
                driver.get("https://labs.google/fx/vi/tools/flow")
                time.sleep(5)
                
            except Exception as e:
                print(f"[Browser] Setup Error: {e}")
                if driver: driver.quit()
                if cache_key and cache_key in self._drivers: del self._drivers[cache_key]
                return None

        # 3. Check / Refresh
        if used_cache:
            try:
                if "labs.google" not in driver.current_url:
                    driver.get("https://labs.google/fx/vi/tools/flow")
                    time.sleep(3)
            except:
                print("[Browser] Cached driver bad state. Killing.")
                driver.quit()
                if cache_key in self._drivers: del self._drivers[cache_key]
                return self.fetch_recaptcha_token(json_cookies, use_visible_browser, cache_key)

        # 4. Wait & Execute JS
        try:
            print("[Browser] Waiting for grecaptcha...")
            grecaptcha_ready = False
            for i in range(40): # 20s wait
                try:
                    # Check if grecaptcha.enterprise is actually ready
                    status = driver.execute_script("""
                        if (typeof grecaptcha === 'undefined') return 'no_grecaptcha';
                        if (typeof grecaptcha.enterprise === 'undefined') return 'no_enterprise';
                        return 'ready';
                    """)
                    if status == 'ready':
                        grecaptcha_ready = True
                        break
                except: pass
                time.sleep(0.5)
            
            if not grecaptcha_ready:
                print(f"[Browser] Timeout: grecaptcha status was {status}. Refreshing once...")
                driver.refresh()
                time.sleep(4)
                # One more try
                for i in range(20):
                    try:
                        if driver.execute_script("return typeof grecaptcha !== 'undefined' && typeof grecaptcha.enterprise !== 'undefined'"):
                            grecaptcha_ready = True
                            break
                    except: pass
                    time.sleep(0.5)
            
            if not grecaptcha_ready:
                print("[Browser] Failed to load grecaptcha after refresh.")
                return None
                
            print("[Browser] Executing Token Request...")
            token_result = driver.execute_script("""
                var done = arguments[0];
                try {
                    grecaptcha.enterprise.ready(async () => {
                        try {
                            console.log("Executing grecaptcha...");
                            const token = await grecaptcha.enterprise.execute('6LcsVL4pAAAAASseC_xVzYQA8n0Yx5W7W5tS-c26', {action: 'VIDEOX_GENERATE_VIDEO'});
                            done({status: 'success', token: token});
                        } catch (e) {
                            done({status: 'error', error: e.toString()});
                        }
                    });
                } catch(e) {
                    done({status: 'script_error', error: e.toString()});
                }
            """)
            
            if not token_result:
                print("[Browser] JS returned NULL result")
                return None
                
            if token_result.get('status') == 'success':
                token = token_result.get('token')
                print(f"[Browser] Token OK: {token[:20]}...")
                return token
            else:
                err = token_result.get('error', 'Unknown error')
                print(f"[Browser] Token JS Error: {err}")
                return None

        except Exception as e:
            print(f"[Browser] Execution Exception: {e}")
            if cache_key:
                try: driver.quit()
                except: pass
                if cache_key in self._drivers: del self._drivers[cache_key]
            return None
        finally:
            if not cache_key:
                driver.quit()

    @classmethod
    def close_all_browsers(cls):
        for k, d in cls._drivers.items():
            try: d.quit()
            except: pass
        cls._drivers.clear()
