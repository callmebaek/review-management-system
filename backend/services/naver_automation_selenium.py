"""
Naver Smart Place Center Automation using Selenium (Python 3.13 compatible!)
⚠️ 주의: 네이버는 공식 리뷰 관리 API를 제공하지 않습니다.
이 모듈은 개인 사용 목적으로만 사용하시기 바랍니다.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import json
import os
import time
import logging
import hashlib
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from config import settings
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class NaverPlaceAutomationSelenium:
    """Naver Smart Place Center automation using Selenium"""
    
    def __init__(self):
        self.session_file = os.path.join(settings.data_dir, "naver_sessions", "session_selenium.json")
        os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
        
        # 🚀 Performance optimization: Cache for places list
        self._places_cache: Optional[List[Dict]] = None
        self._places_cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=5)  # 5분간 캐시 유지

        # 🚀 REVIEWS CACHE (Performance & Pagination Fix)
        # Structure: { f"{place_id}:{filter_type}": { 'data': [...], 'time': datetime, 'total': int } }
        self._reviews_cache: Dict[str, Dict] = {}
        self._reviews_cache_ttl = timedelta(minutes=10)  # 10 minutes cache
        
        # 🚀 PROGRESS TRACKING (Real-time feedback)
        # Structure: { place_id: { 'status': str, 'count': int, 'message': str, 'timestamp': datetime } }
        self._loading_progress: Dict[str, Dict] = {}
    
    def _load_session_from_mongodb(self, user_id="default"):
        """Load session from MongoDB (cloud storage)"""
        try:
            if not settings.use_mongodb or not settings.mongodb_url:
                return None
            
            from utils.db import get_db
            db = get_db()
            if db is None:
                return None
            
            session = db.naver_sessions.find_one({"_id": user_id})
            if session and session.get('cookies'):
                print(f"📦 Found session in MongoDB ({len(session['cookies'])} cookies)")
                return session['cookies']
            
            return None
        except Exception as e:
            logger.error(f"❌ MongoDB session load error: {e}")
            return None
    
    def _create_driver(self, headless=True):
        """Create and configure Chrome WebDriver"""
        print("🌐 Creating Chrome WebDriver...")
        logger.info("🌐 Creating Chrome WebDriver...")
        
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless=new')
        
        # Essential options for Heroku
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Heroku specific
        chrome_options.add_argument('--single-process')
        chrome_options.add_argument('--disable-setuid-sandbox')
        chrome_options.add_argument('--remote-debugging-port=9222')
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Check if running on Heroku (has DYNO environment variable)
        if os.environ.get('DYNO'):
            print("🔧 Detected Heroku environment - using chrome-for-testing paths")
            logger.info("🔧 Detected Heroku environment")
            
            # Heroku chrome-for-testing buildpack sets these environment variables
            chrome_bin = os.environ.get('GOOGLE_CHROME_BIN', '/app/.chrome-for-testing/chrome-linux64/chrome')
            chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', '/app/.chromedriver/bin/chromedriver')
            
            print(f"   Chrome binary: {chrome_bin}")
            print(f"   ChromeDriver: {chromedriver_path}")
            
            chrome_options.binary_location = chrome_bin
            service = Service(executable_path=chromedriver_path)
        else:
            print("💻 Local environment - using ChromeDriverManager")
            # Auto-install ChromeDriver for local development
            service = Service(ChromeDriverManager().install())
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Try to load session (MongoDB first, then local file)
        cookies = None
        
        # Priority 1: Try MongoDB (cloud storage)
        cookies = self._load_session_from_mongodb()
        if cookies:
            print("✅ Using session from MongoDB (cloud)")
        # Priority 2: Try local file (fallback)
        elif os.path.exists(self.session_file):
            print("📂 Using session from local file")
            with open(self.session_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
        
        # Load cookies if found
        if cookies:
            logger.info(f"📂 Loading saved session ({len(cookies)} cookies)...")
            print(f"📂 Loading {len(cookies)} cookies...")
            
            # Step 1: Navigate to Naver domain first
            driver.get('https://www.naver.com')
            time.sleep(1)
            
            # Step 2: Load and add all cookies
            cookies_added = 0
            for cookie in cookies:
                try:
                    # Clean up cookie data for Selenium
                    if 'expiry' in cookie:
                        cookie['expiry'] = int(cookie['expiry'])
                    if 'sameSite' in cookie and cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                        del cookie['sameSite']
                    
                    driver.add_cookie(cookie)
                    cookies_added += 1
                except Exception as e:
                    logger.debug(f"Failed to add cookie {cookie.get('name')}: {e}")
            
            print(f"✅ Added {cookies_added}/{len(cookies)} cookies")
            
            # Step 3: CRITICAL - Refresh page to apply cookies
            print("🔄 Refreshing page to apply cookies...")
            driver.refresh()
            time.sleep(2)
            
            print("✅ Session cookies loaded and applied")
        
        logger.info("✅ WebDriver ready")
        return driver
    
    def _save_session(self, driver):
        """Save browser session"""
        logger.info("💾 Saving session...")
        cookies = driver.get_cookies()
        with open(self.session_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
    
    def login(self, username: str, password: str) -> Dict:
        """Login to Naver"""
        # Check if session already exists and is valid
        if os.path.exists(self.session_file):
            print("🔍 Found existing session, checking validity...")
            logger.info("🔍 Found existing session, checking validity...")
            
            status = self.check_login_status()
            if status.get('logged_in'):
                print("✅ Existing session is valid, login not needed!")
                logger.info("✅ Existing session is valid, login not needed!")
                return {
                    'success': True,
                    'message': 'Already logged in (existing session)'
                }
            else:
                print("⚠️ Existing session expired, re-login required")
                logger.info("⚠️ Existing session expired, re-login required")
        
        driver = None
        try:
            print(f"🔐 Starting Naver login for: {username}")
            logger.info(f"🔐 Starting Naver login for: {username}")
            driver = self._create_driver(headless=False)  # Show browser for 2FA
            print("✅ Driver created successfully")
            
            # Navigate to Naver login
            print("📄 Opening Naver login page...")
            logger.info("📄 Opening Naver login page...")
            driver.get('https://nid.naver.com/nidlogin.login')
            time.sleep(2)
            
            # Fill login form using JavaScript to avoid bot detection
            print("⌨️ Filling login form...")
            logger.info("⌨️ Filling login form...")
            id_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'id'))
            )
            pw_input = driver.find_element(By.ID, 'pw')
            
            # Use JavaScript to set values (more human-like)
            driver.execute_script(f"document.getElementById('id').value = '{username}';")
            time.sleep(0.5)
            driver.execute_script(f"document.getElementById('pw').value = '{password}';")
            time.sleep(0.5)
            
            # Click login button
            print("🖱️ Clicking login button...")
            logger.info("🖱️ Clicking login button...")
            login_btn = driver.find_element(By.CSS_SELECTOR, '.btn_login')
            login_btn.click()
            
            # Wait for login result (longer wait for 2FA)
            print("⏳ Waiting for login result (2차 인증이 필요하면 60초 내에 완료해주세요!)...")
            logger.info("⏳ Waiting for login result (2차 인증 대기)...")
            
            # Wait up to 60 seconds for successful login
            max_wait = 60
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                current_url = driver.current_url
                
                # 🚀 NEW: Handle device registration popup
                if 'deviceConfirm' in current_url:
                    print("📱 Device registration page detected...")
                    try:
                        # Look for "나중에" or "확인" or "등록" button
                        buttons_to_try = [
                            ("//button[contains(., '나중에')]", "나중에"),
                            ("//button[contains(., '확인')]", "확인"),
                            ("//a[contains(., '나중에')]", "나중에 링크"),
                            (".btn_confirm", "확인 버튼"),
                        ]
                        
                        clicked = False
                        for xpath, name in buttons_to_try:
                            try:
                                if xpath.startswith("//"):
                                    btn = driver.find_element(By.XPATH, xpath)
                                else:
                                    btn = driver.find_element(By.CSS_SELECTOR, xpath)
                                driver.execute_script("arguments[0].click();", btn)
                                print(f"  ✅ Clicked '{name}' on device registration page")
                                clicked = True
                                time.sleep(2)
                                break
                            except:
                                continue
                        
                        if not clicked:
                            print("  ⚠️ Could not find button on device registration page")
                            print("  💡 Please click manually in the browser window!")
                            time.sleep(5)  # Give user time to click manually
                            
                    except Exception as e:
                        print(f"  ⚠️ Device registration handling error: {e}")
                    
                    time.sleep(2)
                    continue
                
                # Check if login successful (NOT on login/device pages)
                if 'naver.com' in current_url and 'nidlogin' not in current_url and 'deviceConfirm' not in current_url:
                    print(f"✅ Login successful! (waited {int(time.time() - start_time)}s)")
                    logger.info("✅ Login successful!")
                    break
                
                # Check if still on login page or 2FA page
                if 'nidlogin' in current_url or 'deviceConfirm' in current_url:
                    time.sleep(2)
                    continue
                    
                break
            
            time.sleep(2)  # Extra wait
            
            # Check if login was successful
            current_url = driver.current_url
            page_title = driver.title
            print(f"🔗 Current URL: {current_url}")
            print(f"📄 Page title: {page_title}")
            logger.info(f"🔗 Current URL: {current_url}")
            logger.info(f"📄 Page title: {page_title}")
            
            # 🚀 STRICT CHECK: Must NOT be on login/device pages
            if 'naver.com' in current_url and 'nidlogin' not in current_url and 'deviceConfirm' not in current_url:
                # Login successful
                print("✅ Login successful!")
                logger.info("✅ Login successful!")
                self._save_session(driver)
                return {
                    'success': True,
                    'message': 'Successfully logged in to Naver'
                }
            else:
                # Check for error message
                print("❌ Login failed - checking error message...")
                logger.error("❌ Login failed - checking error message...")
                
                # Try multiple error selectors
                error_msg = None
                for selector in ['.error_message', '.error', '.alert_error', '#err_common']:
                    try:
                        error_elem = driver.find_element(By.CSS_SELECTOR, selector)
                        error_msg = error_elem.text
                        if error_msg:
                            break
                    except:
                        continue
                
                if not error_msg:
                    # Get page source for debugging
                    page_source = driver.page_source[:500]
                    print(f"📄 Page source preview: {page_source}")
                    logger.error(f"📄 Page source preview: {page_source}")
                    error_msg = "Could not detect error message. Please check credentials or try manual login."
                
                print(f"❌ Login failed: {error_msg}")
                logger.error(f"❌ Login failed: {error_msg}")
                return {
                    'success': False,
                    'message': f'Login failed: {error_msg}'
                }
        
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Login error: {error_msg}")
            logger.error(f"❌ Login error: {error_msg}")
            import traceback
            error_trace = traceback.format_exc()
            print(f"Full traceback:\n{error_trace}")
            logger.error(f"Full traceback:\n{error_trace}")
            return {
                'success': False,
                'message': f'Login error: {error_msg}'
            }
        
        finally:
            if driver:
                driver.quit()
    
    def check_login_status(self) -> Dict:
        # ... (Same as before)
        """Check if logged in to Naver (based on session file or MongoDB)"""
        print(f"🔍 Checking session file: {self.session_file}")
        print(f"🔍 Session file exists: {os.path.exists(self.session_file)}")
        
        # Priority 1: Check local session file
        if os.path.exists(self.session_file):
            logger.info("✅ Session file found - assuming logged in")
            print("✅ Session file found - returning logged_in=True")
            return {
                'logged_in': True,
                'message': 'Logged in to Naver (session file found)'
            }
        
        # Priority 2: Check MongoDB session
        try:
            mongodb_session = self._load_session_from_mongodb()
            if mongodb_session:
                logger.info("✅ MongoDB session found - assuming logged in")
                print("✅ MongoDB session found - returning logged_in=True")
                return {
                    'logged_in': True,
                    'message': 'Logged in to Naver (MongoDB session found)'
                }
        except Exception as e:
            logger.error(f"❌ MongoDB session check error: {e}")
            print(f"❌ MongoDB session check error: {e}")
        
        # No session found
        logger.info("❌ No session found")
        print("❌ No session found - returning logged_in=False")
        return {
            'logged_in': False,
            'message': 'No session found. Please login first.'
        }
    
    def get_places(self) -> List[Dict]:
        # ... (Same as before)
        """Get list of places from Smartplace Center (with 5-minute cache)"""
        
        # 🚀 Check cache first
        if self._places_cache is not None and self._places_cache_time is not None:
            cache_age = datetime.now() - self._places_cache_time
            if cache_age < self._cache_ttl:
                print(f"⚡ Using cached places (age: {int(cache_age.total_seconds())}s)")
                logger.info(f"⚡ Using cached places (age: {int(cache_age.total_seconds())}s)")
                return self._places_cache
            else:
                print(f"🔄 Cache expired (age: {int(cache_age.total_seconds())}s), refreshing...")
                logger.info("🔄 Cache expired, refreshing...")
        
        driver = None
        try:
            print("📍 Getting places from Smartplace Center...")
            logger.info("📍 Getting places...")
            driver = self._create_driver(headless=True)
            
            # Go to business list page
            print("🏠 Accessing Smartplace business list...")
            driver.get('https://new.smartplace.naver.com/bizes')
            
            # Wait for initial page load
            print("⏳ Waiting for initial page load...")
            time.sleep(2)
            
            # 🚀 CRITICAL: Handle popup/modal that appears on first visit
            print("🔍 Checking for popups...")
            try:
                # Look for common popup/modal patterns
                popup_button_selectors = [
                    "button.Modal_btn_confirm__uQZFR",  # "확인" button
                    "button[class*='confirm']",
                    "button[class*='close']",
                    ".dimmed button",
                    "[class*='modal'] button"
                ]
                
                for selector in popup_button_selectors:
                    try:
                        popup_btn = driver.find_element(By.CSS_SELECTOR, selector)
                        if popup_btn.is_displayed():
                            print(f"  ✅ Found popup button: {selector}")
                            driver.execute_script("arguments[0].click();", popup_btn)
                            print("  ✅ Popup closed!")
                            time.sleep(1)  # Wait for popup to close
                            break
                    except:
                        continue
            except Exception as e:
                print(f"  ⚠️ No popup found (this is OK): {e}")
            
            # Wait for loading indicator to disappear or content to appear
            # 🚀 Reduced timeout from 30s to 10s
            print("⏳ Waiting for content to load (up to 10 seconds)...")
            max_wait = 10
            start_time = time.time()
            content_loaded = False
            
            while time.time() - start_time < max_wait:
                # Check if there are any links with /bizes/place/ pattern
                try:
                    all_links = driver.find_elements(By.TAG_NAME, "a")
                    place_links = [link for link in all_links if link.get_attribute('href') and '/bizes/place/' in link.get_attribute('href')]
                    
                    if len(place_links) > 0:
                        print(f"✅ Content loaded! Found {len(place_links)} place links")
                        content_loaded = True
                        break
                    else:
                        print(f"⏳ Still loading... ({int(time.time() - start_time)}s elapsed)")
                        time.sleep(1)  # 🚀 Reduced from 2s to 1s
                except:
                    time.sleep(1)
            
            if not content_loaded:
                print("⚠️ Timeout waiting for content to load - trying alternative method")
            
            current_url = driver.current_url
            print(f"🔗 Current URL: {current_url}")
            
            # Check if logged in
            if 'nid.naver.com' in current_url or 'login' in current_url.lower():
                print("❌ Not logged in")
                raise HTTPException(status_code=401, detail="Not logged in")
            
            # Take screenshot for debugging
            screenshot_path = os.path.join(settings.data_dir, "naver_sessions", "bizes_list.png")
            driver.save_screenshot(screenshot_path)
            print(f"📸 Screenshot saved: {screenshot_path}")
            
            # Save page source for debugging
            page_source = driver.page_source
            page_source_file = os.path.join(settings.data_dir, "naver_sessions", "bizes_list.html")
            with open(page_source_file, 'w', encoding='utf-8') as f:
                f.write(page_source)
            print(f"📄 Page source saved: {page_source_file}")
            
            places = []
            
            # Method 1: Try to find place links in <a> tags
            try:
                all_links = driver.find_elements(By.TAG_NAME, "a")
                print(f"📋 Total <a> links found: {len(all_links)}")
                
                place_ids_found = set()
                
                for link in all_links:
                    href = link.get_attribute('href')
                    if href and '/bizes/place/' in href:
                        # Extract place_id from URL
                        import re
                        match = re.search(r'/bizes/place/(\d+)', href)
                        if match:
                            place_id = match.group(1)
                            if place_id not in place_ids_found:
                                place_ids_found.add(place_id)
                                
                                # Try to get place name from link text or nearby element
                                place_name = link.text.strip()
                                if not place_name:
                                    # Try parent element
                                    try:
                                        parent = link.find_element(By.XPATH, '..')
                                        place_name = parent.text.strip()
                                    except:
                                        place_name = f"매장 {place_id}"
                                
                                places.append({
                                    'place_id': place_id,
                                    'name': place_name,
                                    'url': f'https://new.smartplace.naver.com/bizes/place/{place_id}/reviews'
                                })
                                print(f"✅ Found place from link: {place_name} (ID: {place_id})")
                
            except Exception as e:
                print(f"⚠️ Error extracting places from links: {e}")
                logger.error(f"Error extracting places from links: {e}")
            
            # Method 2: Extract place IDs from page source using regex
            if len(places) == 0:
                print("🔍 No places found in links - trying regex extraction from page source...")
                try:
                    import re
                    # Look for place IDs in the page source
                    place_id_pattern = r'/bizes/place/(\d+)'
                    matches = re.finditer(place_id_pattern, page_source)
                    
                    place_ids_found = set()
                    for match in matches:
                        place_id = match.group(1)
                        if place_id not in place_ids_found:
                            place_ids_found.add(place_id)
                            print(f"✅ Found place ID in page source: {place_id}")
                    
                    # For each place ID, try to find the business name
                    for place_id in place_ids_found:
                        # Try to find business name near the place ID in the source
                        # Look for patterns like: "businessName":"..." near the place ID
                        name_pattern = rf'place/{place_id}[^{{}}]*?"businessName":"([^"]+)"'
                        name_match = re.search(name_pattern, page_source)
                        
                        if name_match:
                            place_name = name_match.group(1)
                        else:
                            # Alternative: look for any Korean text near place ID
                            context_pattern = rf'place/{place_id}[^<>]{{0,200}}>([가-힣\s]+)<'
                            context_match = re.search(context_pattern, page_source)
                            if context_match:
                                place_name = context_match.group(1).strip()
                            else:
                                place_name = f"매장 {place_id}"
                        
                        places.append({
                            'place_id': place_id,
                            'name': place_name,
                            'url': f'https://new.smartplace.naver.com/bizes/place/{place_id}/reviews'
                        })
                        print(f"✅ Extracted place: {place_name} (ID: {place_id})")
                
                except Exception as e:
                    print(f"⚠️ Error extracting places from page source: {e}")
                    logger.error(f"Error extracting places from page source: {e}")
            
            print(f"📊 Total places found: {len(places)}")
            logger.info(f"✅ Found {len(places)} places")
            
            # 🚀 Save to cache
            self._places_cache = places
            self._places_cache_time = datetime.now()
            print(f"💾 Cached {len(places)} places for 5 minutes")
            
            return places
            
        except Exception as e:
            print(f"❌ Error getting places: {e}")
            logger.error(f"Error getting places: {e}")
            raise HTTPException(status_code=500, detail=f"Error getting places: {str(e)}")
            
        finally:
            if driver:
                driver.quit()
    
    def get_reviews(self, place_id: str, page: int = 1, page_size: int = 20, filter_type: str = 'all', load_count: int = 300) -> List[Dict]:
        """Get reviews for a place from Smartplace Center (BATCH LOADING + CACHE)
        
        New Strategy: Load specified number of reviews, then filter on frontend
        
        Args:
            place_id: Naver place ID
            page: Page number
            page_size: Reviews per page
            filter_type: 'all' (frontend filters)
            load_count: Number of reviews to load (50/150/300/500/1000)
        """
        print(f"📝 Getting reviews for place: {place_id} (page {page}, size {page_size}, load_count={load_count})")
        
        # 🚀 CRITICAL FIX: Initialize progress BEFORE cache check!
        # This ensures progress is always visible, even when serving from cache
        if place_id not in self._loading_progress or self._loading_progress[place_id]['status'] != 'loading':
            print(f"🔄 Initializing progress for {place_id}")
            self._loading_progress[place_id] = {
                'status': 'loading',
                'count': 0,
                'message': '🚀 시작 중...',
                'timestamp': datetime.now()
            }
        
        # 🚀 STEP 1: Check Cache (Include load_count in key)
        cache_key = f"{place_id}:all:{load_count}"  # Cache by place_id and load_count
        if cache_key in self._reviews_cache:
            cache_entry = self._reviews_cache[cache_key]
            cache_age = datetime.now() - cache_entry['time']
            
            if cache_age < self._reviews_cache_ttl:
                all_cached_reviews = cache_entry['data']
                total_count = cache_entry['total']
                
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                
                # 🚀 SMART EXPANSION: If we need more data than cached, load more!
                if end_idx > len(all_cached_reviews) and len(all_cached_reviews) < total_count:
                    print(f"📚 Need more data: Have {len(all_cached_reviews)}, Need {end_idx}, Total {total_count}")
                    print(f"🔄 Expanding cache by loading 200 more reviews...")
                    # Continue to load more (don't return, fall through to loading logic)
                elif len(all_cached_reviews) > 0:
                    print(f"⚡ Using cached reviews (Items {len(all_cached_reviews)}, Age {int(cache_age.total_seconds())}s)")
                    
                    # 🚀 Update progress to show cache hit
                    self._loading_progress[place_id].update({
                        'status': 'completed',
                        'count': len(all_cached_reviews),
                        'message': f'⚡ 캐시에서 로드 완료 ({len(all_cached_reviews)}개)',
                        'timestamp': datetime.now()
                    })
                    
                    # Return ALL reviews (frontend will paginate)
                    return {
                        'reviews': all_cached_reviews,  # Return ALL (not paginated)
                        'total': total_count
                    }
                else:
                    print(f"🔄 Cache hit but empty. Refreshing just in case...")
            else:
                print(f"⏰ Cache expired (Age {int(cache_age.total_seconds())}s). Refreshing...")
        
        # 🚀 STEP 2: Fetch NEW data (User-specified count)
        # Check if we're expanding existing cache
        existing_reviews = []
        if cache_key in self._reviews_cache:
            existing_reviews = self._reviews_cache[cache_key]['data']
            print(f"📦 Expanding cache: Currently have {len(existing_reviews)} reviews")
        
        # 🚀 USER CHOICE: Load exactly what user requested
        TARGET_LOAD_COUNT = load_count
        
        driver = None
        try:
            # 🚀 CRITICAL: Initialize progress tracking BEFORE anything
            print(f"🔄 Initializing progress tracking for {place_id}")
            self._loading_progress[place_id] = {
                'status': 'loading',
                'count': 0,
                'message': '🚀 브라우저 시작 중...',
                'timestamp': datetime.now()
            }
            logger.info(f"Progress initialized: {self._loading_progress[place_id]}")
            
            driver = self._create_driver(headless=True)
            
            # Update progress
            self._loading_progress[place_id]['message'] = '🔐 세션 로딩 중...'
            print(f"Progress: {self._loading_progress[place_id]['message']}")
            reviews_url = f'https://new.smartplace.naver.com/bizes/place/{place_id}/reviews?menu=visitor'
            print(f"🔗 Accessing: {reviews_url}")
            self._loading_progress[place_id]['message'] = '📄 리뷰 페이지 접속 중...'
            driver.get(reviews_url)
            
            print("⏳ Waiting for reviews page to load...")
            self._loading_progress[place_id]['message'] = '⏳ 페이지 로딩 중...'
            time.sleep(2)
            
            # Handle popup
            try:
                popup_btn = driver.find_element(By.CSS_SELECTOR, "button.Modal_btn_confirm__uQZFR")
                if popup_btn.is_displayed():
                    driver.execute_script("arguments[0].click();", popup_btn)
                    time.sleep(1)
            except:
                pass
            
            # 🚀 NEW STRATEGY: Skip UI filter, load ALL reviews directly
            # This is more stable and efficient than trying to click filters
            print("📜 Loading ALL reviews (작성일순)...")
            target_display = "전체" if TARGET_LOAD_COUNT >= 9999 else f"{TARGET_LOAD_COUNT}개"
            self._loading_progress[place_id].update({
                'status': 'loading',
                'count': 0,
                'message': f'📜 스크롤 준비 중... (목표: {target_display})',
                'timestamp': datetime.now()
            })
            print(f"Progress before scroll: {self._loading_progress[place_id]}")
            
            # 🚀 STEP 3: Scroll Logic (Massive Batch Load)
            print(f"📜 Smart batch loading (Target: {TARGET_LOAD_COUNT})...")
            self._loading_progress[place_id]['message'] = f'📜 스크롤 시작! (목표: {target_display})'
            print(f"Progress at scroll start: {self._loading_progress[place_id]}")
            
            last_count = 0
            no_change = 0
            
            # Adjust scroll attempts based on target
            max_scrolls = 50 if TARGET_LOAD_COUNT <= 50 else \
                         100 if TARGET_LOAD_COUNT <= 150 else \
                         150 if TARGET_LOAD_COUNT <= 300 else \
                         250 if TARGET_LOAD_COUNT <= 500 else \
                         400 if TARGET_LOAD_COUNT <= 1000 else \
                         800  # For "all" (9999)
            
            for i in range(max_scrolls):
                try:
                    lis = driver.find_elements(By.TAG_NAME, "li")
                    current_count = len(lis)
                    
                    if current_count > last_count:
                        # Print every change
                        print(f"  📈 Loaded {current_count} reviews...")
                        
                        # 🚀 ALWAYS update progress (every single change for real-time feel)
                        message = f'📈 {current_count}개 리뷰 로드됨...'
                        self._loading_progress[place_id].update({
                            'status': 'loading',
                            'count': current_count,
                            'message': message,
                            'timestamp': datetime.now()
                        })
                        
                        last_count = current_count
                        no_change = 0
                    else:
                        no_change += 1
                    
                    if current_count >= TARGET_LOAD_COUNT:
                        print(f"  ✅ Reached target {TARGET_LOAD_COUNT}!")
                        break
                        
                    if no_change >= 5:
                        print("  ⚠️ No more content loading.")
                        break
                    
                    # 🚀 FIX: Use scrollIntoView on the LAST element
                    if lis:
                        driver.execute_script("arguments[0].scrollIntoView(true);", lis[-1])
                    else:
                        driver.execute_script("window.scrollBy(0, 1000);")
                        
                    time.sleep(0.5)  # Wait for render
                    
                except Exception as e:
                    print(f"  ⚠️ Scroll error: {e}")
                    break
            
            # 🚀 STEP 4: Parse Data
            print("🔍 Parsing reviews...")
            self._loading_progress[place_id]['message'] = f'📝 {last_count}개 리뷰 파싱 중...'
            all_reviews = []
            
            # Get total count first
            total_count = 0
            try:
                import re
                txt = driver.find_element(By.TAG_NAME, 'body').text
                m = re.search(r'전체\s*(\d+)', txt)
                if m: total_count = int(m.group(1))
            except: pass
            
            lis = driver.find_elements(By.TAG_NAME, "li")
            
            for li in lis:
                try:
                    # Author
                    try:
                        author = li.find_element(By.CLASS_NAME, "pui__JiVbY3").text.strip()
                    except:
                        continue # Skip if no author structure
                        
                    # Date
                    date = "날짜 없음"
                    try:
                        d_elems = li.find_elements(By.CLASS_NAME, "pui__m7nkds")
                        for d in d_elems:
                            if re.search(r'20\d{2}\.', d.text):
                                date = d.text.strip()
                                break
                    except: pass
                    
                    # Content (Relaxed filter)
                    content = ""
                    try:
                        # Click 'more' if exists
                        try:
                            btn = li.find_element(By.CLASS_NAME, "pui__wFzIYl")
                            driver.execute_script("arguments[0].click();", btn)
                        except: pass
                        
                        content = li.find_element(By.CLASS_NAME, "pui__vn15t2").text.strip()
                    except: 
                        content = "" # Allow empty content (Issue #1 fix)

                    # Filter: Valid Author?
                    if not author or author == "익명": continue
                    if "가이드" in author: continue
                    
                    # Filter: Guide message in content?
                    if "답글 잘 다는 방법" in content: continue

                    # Reply
                    reply_text = None
                    reply_date = None
                    try:
                        reply_elem = li.find_element(By.CLASS_NAME, "pui__GbW8H7")
                        full_reply = reply_elem.text
                        
                        # Extract date from reply
                        rd_match = re.search(r'20\d{2}\.\s*\d{1,2}\.\s*\d{1,2}', full_reply)
                        if rd_match:
                            reply_date = rd_match.group(0)
                        
                        reply_text = full_reply
                    except: pass

                    # ID Generation
                    unique_str = f"{author}-{date}-{content[:30]}"
                    rid = hashlib.md5(unique_str.encode()).hexdigest()[:8]
                    
                    # 🚀 NEW STRATEGY: Load ALL reviews, filter on frontend
                    # No server-side filtering - this is more stable and efficient
                    
                    all_reviews.append({
                        'review_id': f"naver-{place_id}-{rid}",
                        'place_id': place_id,
                        'author': author,
                        'date': date,
                        'content': content,
                        'has_reply': bool(reply_text),
                        'reply': reply_text,
                        'reply_date': reply_date
                    })
                    
                except: continue

            # 🚀 MERGE with existing cache if expanding
            if existing_reviews:
                print(f"🔗 Merging {len(all_reviews)} new reviews with {len(existing_reviews)} existing...")
                # Combine existing + new
                combined_reviews = existing_reviews + all_reviews
            else:
                combined_reviews = all_reviews
            
            # Deduplicate
            unique_reviews = []
            seen = set()
            for r in combined_reviews:
                if r['review_id'] not in seen:
                    seen.add(r['review_id'])
                    unique_reviews.append(r)
            
            # 🚀 ROBUST SORTING by date (newest first)
            def parse_review_date(date_str):
                """Parse Korean date format: '2025. 12. 9' or '2025. 9. 8(화)'"""
                try:
                    # Remove day of week if present: '2025. 12. 9(화)' -> '2025. 12. 9'
                    date_str = re.sub(r'\([월화수목금토일]\)', '', date_str).strip()
                    # Remove extra spaces and dots: '2025. 12. 9' -> '2025-12-09'
                    parts = [p.strip() for p in date_str.replace('.', '').split() if p.strip()]
                    if len(parts) >= 3:
                        year, month, day = parts[0], parts[1].zfill(2), parts[2].zfill(2)
                        return f"{year}-{month}-{day}"
                except:
                    pass
                return "1900-01-01"  # Fallback for unparseable dates
            
            try:
                unique_reviews.sort(key=lambda x: parse_review_date(x['date']), reverse=True)
                print(f"✅ Sorted {len(unique_reviews)} reviews by date (newest first)")
            except Exception as e:
                print(f"⚠️ Sort warning: {e}")
            
            # 🚀 STEP 5: Update Cache (Specific to filter)
            self._reviews_cache[cache_key] = {
                'data': unique_reviews,
                'time': datetime.now(),
                'total': total_count if total_count > 0 else len(unique_reviews)
            }
            print(f"💾 Cached {len(unique_reviews)} reviews for {cache_key}")
            
            # 🚀 Return ALL reviews (frontend will handle filtering + pagination)
            # This allows filter to work across all loaded reviews
            
            # 🚀 Mark as completed
            self._loading_progress[place_id] = {
                'status': 'completed',
                'count': len(unique_reviews),
                'message': f'✅ {len(unique_reviews)}개 리뷰 로드 완료!',
                'timestamp': datetime.now()
            }
            
            return {
                'reviews': unique_reviews,  # Return ALL reviews (not paginated)
                'total': self._reviews_cache[cache_key]['total']
            }
        
        except Exception as e:
            print(f"❌ Error: {e}")
            # 🚀 Mark as error
            self._loading_progress[place_id] = {
                'status': 'error',
                'count': 0,
                'message': f'❌ 오류: {str(e)[:50]}',
                'timestamp': datetime.now()
            }
            raise HTTPException(status_code=500, detail=str(e))
        
        finally:
            if driver:
                driver.quit()
    
    def post_reply(self, place_id: str, review_id: str, reply_text: str) -> Dict:
        """Post a reply to a review in Smartplace Center"""
        driver = None
        try:
            print(f"💬 Posting reply to review: {review_id}")
            logger.info(f"💬 Posting reply to review: {review_id}")
            
            driver = self._create_driver(headless=True)
            
            # Go to Smartplace reviews page (NOT mobile version)
            reviews_url = f'https://new.smartplace.naver.com/bizes/place/{place_id}/reviews?menu=visitor'
            print(f"🔗 Opening: {reviews_url}")
            driver.get(reviews_url)
            time.sleep(2)
            
            # Handle popup
            try:
                popup_btn = driver.find_element(By.CSS_SELECTOR, "button.Modal_btn_confirm__uQZFR")
                if popup_btn.is_displayed():
                    driver.execute_script("arguments[0].click();", popup_btn)
                    time.sleep(1)
            except:
                pass
            
            # Find all review cards
            print("🔍 Finding target review...")
            all_lis = driver.find_elements(By.TAG_NAME, "li")
            
            target_review = None
            target_author = None
            
            # Extract author and date from review_id for more flexible matching
            # Try multiple matching strategies
            
            for li in all_lis:
                try:
                    # Get review data
                    author = li.find_element(By.CLASS_NAME, "pui__JiVbY3").text.strip()
                    date = "날짜 없음"
                    try:
                        d_elems = li.find_elements(By.CLASS_NAME, "pui__m7nkds")
                        for d in d_elems:
                            if re.search(r'20\d{2}\.', d.text):
                                date = d.text.strip()
                                break
                    except: pass
                    
                    content = ""
                    try:
                        content = li.find_element(By.CLASS_NAME, "pui__vn15t2").text.strip()[:30]
                    except: pass
                    
                    # Generate ID to match (exact match)
                    unique_str = f"{author}-{date}-{content}"
                    rid = hashlib.md5(unique_str.encode()).hexdigest()[:8]
                    generated_id = f"naver-{place_id}-{rid}"
                    
                    if generated_id == review_id:
                        print(f"✅ Found target review (exact match): {author}")
                        target_review = li
                        target_author = author
                        break
                    
                    # Fallback: Try with empty content (in case content parsing differs)
                    fallback_str = f"{author}-{date}-"
                    fallback_rid = hashlib.md5(fallback_str.encode()).hexdigest()[:8]
                    fallback_id = f"naver-{place_id}-{fallback_rid}"
                    
                    if fallback_id == review_id:
                        print(f"✅ Found target review (fallback match): {author}")
                        target_review = li
                        target_author = author
                        break
                        
                except:
                    continue
            
            if not target_review:
                raise Exception(f"Could not find review with ID: {review_id}")
            
            # Scroll to review
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_review)
            time.sleep(0.5)
            
            # Click reply button: "답글 쓰기"
            print("🖱️  Clicking '답글 쓰기' button...")
            reply_btn = target_review.find_element(By.XPATH, ".//button[contains(., '답글')]")
            driver.execute_script("arguments[0].click();", reply_btn)
            time.sleep(1)
            
            # Find textarea (should appear after clicking)
            print("⌨️  Filling reply text...")
            textarea = target_review.find_element(By.TAG_NAME, "textarea")
            textarea.clear()
            textarea.send_keys(reply_text)
            time.sleep(0.5)
            
            # Click submit button: "등록"
            print("📤 Clicking '등록' button...")
            submit_btn = target_review.find_element(By.XPATH, ".//button[contains(., '등록')]")
            driver.execute_script("arguments[0].click();", submit_btn)
            time.sleep(2)
            
            # Check for success (reply should now appear)
            try:
                reply_elem = target_review.find_element(By.CLASS_NAME, "pui__GbW8H7")
                print(f"✅ Reply posted successfully! Reply text: {reply_elem.text[:50]}...")
            except:
                print("⚠️ Could not verify reply immediately (might need refresh)")
            
            # 🚀 UPDATE cache instead of clearing it (better UX)
            # Find the review in cache and update has_reply
            # Note: We need to update ALL cache entries for this place_id
            cache_keys_to_update = [k for k in self._reviews_cache.keys() if k.startswith(f"{place_id}:")]
            
            updated = False
            for cache_key in cache_keys_to_update:
                if cache_key in self._reviews_cache:
                    for review in self._reviews_cache[cache_key]['data']:
                        if review['review_id'] == review_id:
                            review['has_reply'] = True
                            review['reply'] = reply_text
                            review['reply_date'] = datetime.now().strftime('%Y. %m. %d')
                            print(f"✅ Updated review {review_id} in cache ({cache_key})")
                            updated = True
            
            if not updated:
                print(f"⚠️ No cache found for place {place_id}, will refresh on next load")
            
            # Rate limiting
            time.sleep(settings.naver_rate_limit_delay)
            
            logger.info("✅ Reply posted")
            return {
                'success': True,
                'message': 'Reply posted successfully',
                'review_id': review_id
            }
        
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error posting reply: {error_msg}")
            logger.error(f"Error posting reply: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Error posting reply: {error_msg}")
        
        finally:
            if driver:
                driver.quit()
    
    def get_loading_progress(self, place_id: str) -> Dict:
        """Get current loading progress for a place"""
        if place_id in self._loading_progress:
            progress = self._loading_progress[place_id]
            # Clean up completed/error status after 30 seconds (longer to ensure frontend sees it)
            if progress['status'] in ['completed', 'error']:
                age = datetime.now() - progress['timestamp']
                if age > timedelta(seconds=30):
                    del self._loading_progress[place_id]
                    return {'status': 'idle', 'count': 0, 'message': ''}
            return progress
        else:
            return {'status': 'idle', 'count': 0, 'message': ''}
    
    def logout(self) -> Dict:
        """Logout and clear session"""
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            
            # 🚀 Clear cache on logout
            self._places_cache = None
            self._places_cache_time = None
            self._reviews_cache = {}  # Clear reviews cache too
            self._loading_progress = {}  # Clear progress too
            print("🗑️ Cache cleared on logout")
            
            return {
                'success': True,
                'message': 'Successfully logged out'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error logging out: {str(e)}'
            }


# Create singleton instance
naver_automation_selenium = NaverPlaceAutomationSelenium()
