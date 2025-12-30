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
        
        # 🚀 Multi-account support
        self.active_user_id = "default"  # Default user
        
        # 🔒 Thread Lock for race condition prevention
        import threading
        self._user_lock = threading.Lock()  # API 호출 간 user_id 보호
        
        # 🚀 Performance optimization: Cache for places list (user별로 분리!)
        self._places_cache: Dict[str, List[Dict]] = {}  # {user_id: [places]}
        self._places_cache_time: Dict[str, datetime] = {}  # {user_id: datetime}
        self._cache_ttl = timedelta(minutes=5)  # 5분간 캐시 유지

        # 🚀 REVIEWS CACHE (Performance & Pagination Fix)
        # Structure: { f"{place_id}:{filter_type}": { 'data': [...], 'time': datetime, 'total': int } }
        self._reviews_cache: Dict[str, Dict] = {}
        self._reviews_cache_ttl = timedelta(minutes=10)  # 10 minutes cache
        
        # 🚀 PROGRESS TRACKING (Real-time feedback)
        # Structure: { place_id: { 'status': str, 'count': int, 'message': str, 'timestamp': datetime } }
        self._loading_progress: Dict[str, Dict] = {}
    
    def _load_session_from_mongodb(self, user_id="default"):
        """Load session from MongoDB (cloud storage)
        
        Returns:
            dict with 'cookies', 'user_agent', 'window_size' or None
        """
        try:
            if not settings.use_mongodb or not settings.mongodb_url:
                return None
            
            from utils.db import get_db
            db = get_db()
            if db is None:
                return None
            
            session = db.naver_sessions.find_one({"_id": user_id})
            if session and session.get('cookies'):
                print(f"📦 Found session in MongoDB for user '{user_id}' ({len(session['cookies'])} cookies)")
                
                # 🔧 CRITICAL: User-Agent와 window_size도 함께 반환
                user_agent = session.get('user_agent')
                window_size = session.get('window_size')
                
                if user_agent:
                    print(f"   ✅ User-Agent: {user_agent[:80]}...")
                if window_size:
                    print(f"   ✅ Window Size: {window_size}")
                
                # Update last_used timestamp
                db.naver_sessions.update_one(
                    {"_id": user_id},
                    {"$set": {"last_used": datetime.utcnow()}}
                )
                
                return {
                    'cookies': session['cookies'],
                    'user_agent': user_agent,
                    'window_size': window_size
                }
            
            return None
        except Exception as e:
            logger.error(f"❌ MongoDB session load error: {e}")
            return None
    
    def set_active_user(self, user_id="default"):
        """Set the active user ID for this session"""
        self.active_user_id = user_id
        print(f"🔄 Active user switched to: {user_id}")
    
    def _create_driver(self, headless=True, user_id=None):
        """
        Create and configure Chrome WebDriver
        
        Args:
            headless: Run in headless mode
            user_id: User ID for session loading (if None, uses self.active_user_id)
        """
        # 🔒 user_id 파라미터 우선 사용 (race condition 방지)
        effective_user_id = user_id if user_id else self.active_user_id
        
        print(f"🌐 Creating Chrome WebDriver for user: {effective_user_id}")
        logger.info(f"🌐 Creating Chrome WebDriver for user: {effective_user_id}")
        
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
        
        # Heroku specific - Memory optimization
        chrome_options.add_argument('--single-process')
        chrome_options.add_argument('--disable-setuid-sandbox')
        chrome_options.add_argument('--remote-debugging-port=9222')
        
        # Additional memory saving options for Heroku
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-breakpad')
        chrome_options.add_argument('--disable-component-extensions-with-background-pages')
        chrome_options.add_argument('--disable-features=TranslateUI,BlinkGenPropertyTrees')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--enable-features=NetworkService,NetworkServiceInProcess')
        chrome_options.add_argument('--force-color-profile=srgb')
        chrome_options.add_argument('--hide-scrollbars')
        chrome_options.add_argument('--metrics-recording-only')
        chrome_options.add_argument('--mute-audio')
        
        # Set memory limits
        chrome_options.add_argument('--max_old_space_size=256')
        chrome_options.add_argument('--js-flags=--max-old-space-size=256')
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 🔧 CRITICAL: 기본값 설정 (MongoDB에서 로드한 값으로 나중에 덮어쓸 수 있음)
        default_window_size = '1280,720'  # Reduced from 1920x1080
        default_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        
        chrome_options.add_argument(f'--window-size={default_window_size}')
        chrome_options.add_argument(f'--user-agent={default_user_agent}')
        
        # 🔧 CRITICAL: MongoDB에서 세션 메타데이터 로드 후 Chrome 옵션 업데이트
        session_data = None
        cookies = None
        
        # Priority 1: Try MongoDB (cloud storage) with effective user ID
        session_data = self._load_session_from_mongodb(effective_user_id)
        if session_data:
            print(f"✅ Using session from MongoDB (cloud) for user: {effective_user_id}")
            cookies = session_data.get('cookies')
            
            # 🔧 CRITICAL: 실제 세션 생성 시 사용한 User-Agent와 해상도 적용
            saved_user_agent = session_data.get('user_agent')
            saved_window_size = session_data.get('window_size')
            
            if saved_user_agent:
                print(f"   🔧 Applying saved User-Agent: {saved_user_agent[:80]}...")
                # User-Agent 재설정
                for i, arg in enumerate(chrome_options.arguments):
                    if arg.startswith('--user-agent='):
                        chrome_options.arguments[i] = f'--user-agent={saved_user_agent}'
                        break
            
            if saved_window_size:
                print(f"   🔧 Applying saved Window Size: {saved_window_size}")
                # Window Size 재설정
                for i, arg in enumerate(chrome_options.arguments):
                    if arg.startswith('--window-size='):
                        chrome_options.arguments[i] = f'--window-size={saved_window_size}'
                        break
        
        # Priority 2: Try local file (fallback)
        elif os.path.exists(self.session_file):
            print("📂 Using session from local file")
            with open(self.session_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
        
        # 🔧 CRITICAL: Chrome 옵션 적용 후 드라이버 생성
        # Check if running on Heroku (has DYNO environment variable)
        if os.environ.get('DYNO'):
            print("🔧 Detected Heroku environment - using chrome-for-testing paths")
            logger.info("🔧 Detected Heroku environment")
            
            # chrome-for-testing buildpack installs both Chrome and ChromeDriver in the same directory
            chrome_base = '/app/.chrome-for-testing'
            chrome_bin = f'{chrome_base}/chrome-linux64/chrome'
            chromedriver_path = f'{chrome_base}/chromedriver-linux64/chromedriver'
            
            print(f"   Chrome binary: {chrome_bin}")
            print(f"   ChromeDriver: {chromedriver_path}")
            
            # Verify files exist
            if os.path.exists(chrome_bin):
                print(f"   ✅ Chrome binary found")
            else:
                print(f"   ❌ Chrome binary NOT found at {chrome_bin}")
                # Try to find it
                import glob
                chrome_files = glob.glob('/app/.chrome-for-testing/**/chrome', recursive=True)
                print(f"   Found Chrome at: {chrome_files}")
            
            if os.path.exists(chromedriver_path):
                print(f"   ✅ ChromeDriver found")
            else:
                print(f"   ❌ ChromeDriver NOT found at {chromedriver_path}")
                # Try to find it
                import glob
                driver_files = glob.glob('/app/.chrome-for-testing/**/chromedriver', recursive=True)
                print(f"   Found ChromeDriver at: {driver_files}")
            
            chrome_options.binary_location = chrome_bin
            service = Service(executable_path=chromedriver_path)
        else:
            print("💻 Local environment - using ChromeDriverManager")
            # Auto-install ChromeDriver for local development
            service = Service(ChromeDriverManager().install())
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Load cookies if found
        if cookies:
            logger.info(f"📂 Loading saved session ({len(cookies)} cookies)...")
            print(f"📂 Loading {len(cookies)} cookies...")
            
            # Step 1: Navigate to Naver domain first
            driver.get('https://www.naver.com')
            time.sleep(1)
            
            # Step 2: Load and add all cookies
            cookies_added = 0
            failed_cookies = []
            critical_cookies = ['NID_AUT', 'NID_SES', 'NID_JKL']  # 네이버 인증 핵심 쿠키
            
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
                    cookie_name = cookie.get('name', 'unknown')
                    failed_cookies.append(cookie_name)
                    
                    # 🔧 CRITICAL: 중요 쿠키 실패 시 경고
                    if cookie_name in critical_cookies:
                        logger.error(f"❌ CRITICAL: Failed to add important cookie '{cookie_name}': {e}")
                        print(f"❌ CRITICAL: Failed to add important cookie '{cookie_name}': {e}")
                    else:
                        logger.debug(f"Failed to add cookie {cookie_name}: {e}")
            
            print(f"✅ Added {cookies_added}/{len(cookies)} cookies")
            
            # 🔧 실패한 쿠키 로깅
            if failed_cookies:
                print(f"⚠️ Failed to add {len(failed_cookies)} cookies: {', '.join(failed_cookies)}")
                logger.warning(f"Failed cookies: {', '.join(failed_cookies)}")
                
                # 중요 쿠키가 실패했으면 세션이 제대로 작동하지 않을 수 있음
                critical_failed = [c for c in failed_cookies if c in critical_cookies]
                if critical_failed:
                    print(f"❌ WARNING: Critical authentication cookies failed: {', '.join(critical_failed)}")
                    print(f"   → Session may not work properly!")
                    logger.error(f"Critical cookies failed: {', '.join(critical_failed)}")
            
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
        
        # Priority 2: Check MongoDB session (using active user ID)
        try:
            # 🔧 CRITICAL: MongoDB에서 직접 세션 조회하여 만료 시간 확인
            from utils.db import get_db
            db = get_db()
            if db is not None:
                session = db.naver_sessions.find_one({"_id": self.active_user_id})
                if session:
                    # 만료 시간 확인
                    expires_at = session.get('expires_at')
                    if expires_at:
                        # 🔧 FIX: expires_at이 datetime 객체인지 확인
                        if isinstance(expires_at, str):
                            # 문자열이면 파싱
                            try:
                                # ISO 형식 파싱 (Z 제거 후 UTC로 처리)
                                expires_at_str = expires_at.replace('Z', '')
                                expires_at = datetime.fromisoformat(expires_at_str)
                            except:
                                expires_at = datetime.utcnow() + timedelta(days=7)  # 기본값
                        
                        now = datetime.utcnow()
                        # 타임존 정보가 없으면 naive datetime으로 비교 (둘 다 UTC)
                        # MongoDB에서 가져온 datetime은 보통 naive이므로 그대로 비교
                        
                        if now > expires_at:
                            print(f"⚠️ Session expired for user '{self.active_user_id}' (expired at: {expires_at})")
                            logger.warning(f"Session expired for user: {self.active_user_id}")
                            return {
                                'logged_in': False,
                                'message': f'세션이 만료되었습니다 (만료일: {expires_at.strftime("%Y-%m-%d")}). 새로운 세션을 업로드해주세요.',
                                'expired': True,
                                'expires_at': expires_at.isoformat()
                            }
                        else:
                            remaining_days = (expires_at - now).days
                            print(f"✅ MongoDB session valid for user '{self.active_user_id}' (remaining: {remaining_days} days)")
                    
                    # 🔧 FIX: 쿠키 만료 시간도 확인 (더 정확한 검증)
                    cookies = session.get('cookies', [])
                    if cookies:
                        # 핵심 쿠키의 만료 시간 확인
                        critical_cookies = ['NID_AUT', 'NID_SES', 'NID_JKL']
                        all_critical_valid = True
                        
                        for cookie in cookies:
                            cookie_name = cookie.get('name', '')
                            if cookie_name in critical_cookies:
                                cookie_expiry = cookie.get('expiry')
                                if cookie_expiry:
                                    if isinstance(cookie_expiry, (int, float)):
                                        cookie_expiry_dt = datetime.fromtimestamp(cookie_expiry)
                                        if datetime.utcnow() > cookie_expiry_dt:
                                            print(f"⚠️ Critical cookie '{cookie_name}' expired")
                                            all_critical_valid = False
                                            break
                        
                        if not all_critical_valid:
                            print(f"⚠️ Some critical cookies expired for user '{self.active_user_id}'")
                            return {
                                'logged_in': False,
                                'message': '세션 쿠키가 만료되었습니다. 새로운 세션을 업로드해주세요.',
                                'expired': True
                            }
                    
                    logger.info(f"✅ MongoDB session found for user: {self.active_user_id}")
                    print(f"✅ MongoDB session found for user '{self.active_user_id}' - returning logged_in=True")
                    return {
                        'logged_in': True,
                        'message': f'Logged in to Naver (MongoDB session found for {self.active_user_id})',
                        'active_user': self.active_user_id
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
        """Get list of places from Smartplace Center (with 5-minute cache)"""
        
        # 🔒 Lock으로 race condition 방지
        with self._user_lock:
            current_user_id = self.active_user_id  # Race condition 방지
            print(f"🔒 Acquired lock for get_places() - user: {current_user_id}")
            
            # 🚀 Check cache first (user별로 확인!)
            if current_user_id in self._places_cache and current_user_id in self._places_cache_time:
                cache_age = datetime.now() - self._places_cache_time[current_user_id]
                if cache_age < self._cache_ttl:
                    print(f"⚡ Using cached places for user {current_user_id} (age: {int(cache_age.total_seconds())}s)")
                    logger.info(f"⚡ Using cached places for user {current_user_id} (age: {int(cache_age.total_seconds())}s)")
                    return self._places_cache[current_user_id]
                else:
                    print(f"🔄 Cache expired for user {current_user_id} (age: {int(cache_age.total_seconds())}s), refreshing...")
                    logger.info(f"🔄 Cache expired for user {current_user_id}, refreshing...")
            
            driver = None
            driver_is_persistent = False
            
            try:
                # current_user_id는 위에서 이미 선언됨 (Lock 내부)
                print(f"📍 Getting places from Smartplace Center for user: {current_user_id}")
                logger.info(f"📍 Getting places for user: {current_user_id}")
                
                # 🚀 PERSISTENT BROWSER: 먼저 기존 브라우저 확인
                from services.persistent_browser_manager import browser_manager
                
                driver = browser_manager.get_browser(current_user_id)
                
                if driver:
                    print(f"♻️ Reusing persistent browser for {current_user_id}")
                    driver_is_persistent = True
                else:
                    print(f"🆕 Creating new browser for {current_user_id} (no persistent browser)")
                    driver = self._create_driver(headless=True, user_id=current_user_id)
                    driver_is_persistent = False
                
                # Go to business list page
                print("🏠 Accessing Smartplace business list...")
                driver.get('https://new.smartplace.naver.com/bizes')
                
                # 🔧 CRITICAL: 즉시 세션 유효성 검증 (로그인 페이지 리다이렉트 확인)
                time.sleep(2)  # 리다이렉트가 발생할 수 있는 시간
                current_url = driver.current_url
                print(f"🔗 Current URL after load: {current_url}")
                
                if 'nid.naver.com' in current_url or 'login' in current_url.lower():
                    print("❌ Session expired - redirected to login page")
                    logger.error(f"Session expired for user {current_user_id}")
                    raise HTTPException(
                        status_code=401, 
                        detail=f"네이버 세션이 만료되었습니다. 세션 생성기(EXE)를 사용해서 새로운 세션을 업로드해주세요. (User: {current_user_id})"
                    )
                
                # Wait for initial page load
                print("⏳ Waiting for initial page load...")
                time.sleep(0.5)
                
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
                
                # 🚀 Save to cache (user별로 저장!)
                self._places_cache[current_user_id] = places
                self._places_cache_time[current_user_id] = datetime.now()
                print(f"💾 Cached {len(places)} places for user {current_user_id} (5 minutes)")
                
                return places
                
            except Exception as e:
                print(f"❌ Error getting places: {e}")
                logger.error(f"Error getting places: {e}")
                raise HTTPException(status_code=500, detail=f"Error getting places: {str(e)}")
                
            finally:
                # 🚀 PERSISTENT BROWSER: persistent browser는 닫지 않음!
                if driver and not driver_is_persistent:
                    driver.quit()
                    print("🔒 Closed temporary browser")
                elif driver and driver_is_persistent:
                    print("♻️ Keeping persistent browser alive")
    
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
        driver_is_persistent = False
        current_user_id = self.active_user_id  # race condition 방지
        
        try:
            # 🚀 CRITICAL: Initialize progress tracking BEFORE anything
            print(f"🔄 Initializing progress tracking for {place_id}, user: {current_user_id}")
            self._loading_progress[place_id] = {
                'status': 'loading',
                'count': 0,
                'message': '🚀 브라우저 시작 중...',
                'timestamp': datetime.now()
            }
            logger.info(f"Progress initialized: {self._loading_progress[place_id]}")
            
            # 🚀 PERSISTENT BROWSER: 먼저 기존 브라우저 확인
            from services.persistent_browser_manager import browser_manager
            
            driver = browser_manager.get_browser(current_user_id)
            
            if driver:
                print(f"♻️ Reusing persistent browser for {current_user_id}")
                driver_is_persistent = True
            else:
                print(f"🆕 Creating new browser for {current_user_id} (no persistent browser)")
                driver = self._create_driver(headless=True, user_id=current_user_id)
                driver_is_persistent = False
            
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
            
            # 🚀 STEP 3: Scroll Logic (Smart Adaptive Loading)
            print(f"📜 Smart batch loading (Target: {TARGET_LOAD_COUNT})...")
            self._loading_progress[place_id]['message'] = f'📜 스크롤 시작! (목표: {target_display})'
            print(f"Progress at scroll start: {self._loading_progress[place_id]}")
            
            last_count = 0
            no_change = 0
            skip_ratio = None  # 스킵 비율 (동적 추정)
            estimated_valid_count = 0  # 추정된 유효 리뷰 개수
            sample_parsed = False  # 샘플 파싱 완료 여부
            
            # 🚀 최적화: 초기 목표는 보수적으로 설정 (나중에 조정)
            INITIAL_TARGET = int(TARGET_LOAD_COUNT * 1.8)  # 2.5 → 1.8로 감소 (초기)
            ADJUSTED_TARGET = INITIAL_TARGET
            
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
                        if estimated_valid_count > 0:
                            message += f' (추정 유효: {estimated_valid_count}개)'
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
                    
                    # 🚀 NEW: 샘플 파싱으로 스킵 비율 추정 (15개 이상 로드 시 1회만, 더 빠르게)
                    if not sample_parsed and current_count >= 15:
                        print(f"  🔍 샘플 파싱 시작 (스킵 비율 추정, {current_count}개 중)...")
                        try:
                            sample_size = min(15, current_count)  # 처음 15개 샘플 (더 빠르게)
                            valid_count = 0
                            
                            for li in lis[:sample_size]:
                                try:
                                    author = li.find_element(By.CLASS_NAME, "pui__JiVbY3").text.strip()
                                    if author and author != "익명" and "가이드" not in author:
                                        valid_count += 1
                                except:
                                    pass
                            
                            if sample_size > 0:
                                skip_ratio = 1.0 - (valid_count / sample_size)
                                # 스킵 비율 기반으로 목표 재계산 (15% 여유만)
                                if skip_ratio > 0:
                                    ADJUSTED_TARGET = int(TARGET_LOAD_COUNT / (1.0 - skip_ratio) * 1.15)  # 15% 여유
                                    print(f"  ✅ 샘플 분석: {valid_count}/{sample_size} 유효 (스킵 비율: {skip_ratio:.1%})")
                                    print(f"  🎯 목표 조정: {INITIAL_TARGET} → {ADJUSTED_TARGET}개 (효율적!)")
                                else:
                                    ADJUSTED_TARGET = int(TARGET_LOAD_COUNT * 1.1)  # 스킵이 거의 없으면 10%만 여유
                                    print(f"  ✅ 샘플 분석: 스킵 거의 없음, 목표: {ADJUSTED_TARGET}개")
                            
                            sample_parsed = True
                        except Exception as e:
                            print(f"  ⚠️ 샘플 파싱 오류: {e}, 기본 목표 사용")
                    
                    # 🚀 동적 목표 확인 (추정된 스킵 비율 반영, 매 스크롤마다 확인)
                    if skip_ratio is not None and current_count >= 10:
                        # 현재까지의 유효 리뷰 개수 추정
                        estimated_valid_count = int(current_count * (1.0 - skip_ratio))
                        
                        # 목표에 도달했으면 조기 종료
                        if estimated_valid_count >= TARGET_LOAD_COUNT:
                            print(f"  ✅ 추정 유효 리뷰 {estimated_valid_count}개 도달! (목표: {TARGET_LOAD_COUNT}개)")
                            print(f"     조기 종료로 시간 절약 (불필요한 스크롤 {ADJUSTED_TARGET - current_count}개 생략)")
                            break
                    
                    # 기존 목표 도달 확인
                    if current_count >= ADJUSTED_TARGET:
                        print(f"  ✅ Reached adjusted target {ADJUSTED_TARGET} (raw count, before filtering)")
                        print(f"     Expected after filtering: ~{TARGET_LOAD_COUNT} reviews")
                        break
                        
                    # 🔧 FIX: 더 많은 시도 허용 (5 → 10)
                    if no_change >= 10:  # 5 → 10으로 증가
                        print(f"  ⚠️ No more content loading after {no_change} attempts.")
                        # 목표 개수에 도달하지 못했지만 더 이상 로드할 것이 없으면 중단
                        if current_count < ADJUSTED_TARGET:
                            print(f"  ⚠️ Warning: Only loaded {current_count} items, target was {ADJUSTED_TARGET}")
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
            print(f"🔍 Parsing {last_count} <li> elements...")
            self._loading_progress[place_id]['message'] = f'📝 {last_count}개 리뷰 파싱 중...'
            all_reviews = []
            
            # 🔧 DEBUG: 스킵 카운터
            skip_reasons = {
                'no_author': 0,
                'anonymous': 0,
                'guide': 0,
                'guide_message': 0,
                'parse_error': 0
            }
            
            # Get total count first
            total_count = 0
            try:
                import re
                txt = driver.find_element(By.TAG_NAME, 'body').text
                m = re.search(r'전체\s*(\d+)', txt)
                if m: total_count = int(m.group(1))
            except: pass
            
            lis = driver.find_elements(By.TAG_NAME, "li")
            total_li_count = len(lis)
            
            # 🚀 파싱 중 진행률 업데이트를 위한 카운터
            parsed_count = 0
            update_interval = max(1, total_li_count // 20)  # 20번 정도 업데이트
            
            for idx, li in enumerate(lis):
                try:
                    # Author
                    try:
                        author = li.find_element(By.CLASS_NAME, "pui__JiVbY3").text.strip()
                    except:
                        skip_reasons['no_author'] += 1
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
                    if not author:
                        skip_reasons['no_author'] += 1
                        continue
                    if author == "익명":
                        skip_reasons['anonymous'] += 1
                        continue
                    if "가이드" in author:
                        skip_reasons['guide'] += 1
                        continue
                    
                    # Filter: Guide message in content?
                    if "답글 잘 다는 방법" in content:
                        skip_reasons['guide_message'] += 1
                        continue

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
                    
                    # 🚀 파싱 중 진행률 업데이트 (실제 유효한 리뷰 개수)
                    parsed_count += 1
                    if parsed_count % update_interval == 0 or parsed_count == 1:
                        self._loading_progress[place_id].update({
                            'status': 'loading',
                            'count': parsed_count,  # 실제 파싱된 리뷰 개수
                            'message': f'📝 {parsed_count}개 리뷰 파싱 중... ({idx+1}/{total_li_count})',
                            'timestamp': datetime.now()
                        })
                    
                except Exception as parse_err:
                    skip_reasons['parse_error'] += 1
                    continue

            # 🔧 DEBUG: 스킵 통계 출력
            total_skipped = sum(skip_reasons.values())
            print(f"📊 Parsing complete: {len(all_reviews)} valid reviews, {total_skipped} skipped")
            if total_skipped > 0:
                print(f"   Skip breakdown:")
                for reason, count in skip_reasons.items():
                    if count > 0:
                        print(f"      - {reason}: {count}")
            
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
            
            # 🔧 FIX: 필터링 후 개수 확인 및 경고
            if len(unique_reviews) < TARGET_LOAD_COUNT:
                shortage = TARGET_LOAD_COUNT - len(unique_reviews)
                print(f"⚠️ WARNING: Requested {TARGET_LOAD_COUNT} reviews, but only {len(unique_reviews)} valid reviews found after filtering!")
                print(f"   Missing: {shortage} reviews (likely filtered out as 익명/가이드)")
                logger.warning(f"Review shortage: Requested {TARGET_LOAD_COUNT}, got {len(unique_reviews)}")
            
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
            # 🚀 PERSISTENT BROWSER: persistent browser는 닫지 않음!
            if driver and not driver_is_persistent:
                driver.quit()
                print("🔒 Closed temporary browser")
            elif driver and driver_is_persistent:
                print("♻️ Keeping persistent browser alive")
    
    def post_reply_by_composite(self, place_id: str, author: str, date: str, content: str, reply_text: str, user_id: str = None, expected_count: int = 50) -> Dict:
        """
        작성자 + 날짜 + 내용 3중 매칭으로 답글 게시 (가장 확실한 방법)
        expected_count만큼 리뷰를 렌더링하여 찾기
        """
        import re
        
        # 🔒 현재 user_id 미리 저장 (race condition 방지)
        if user_id:
            self.set_active_user(user_id)
        current_user_id = self.active_user_id
        
        driver = None
        driver_is_persistent = False
        
        try:
            print(f"💬 Posting reply to: {author} ({date}) for user: {current_user_id}")
            print(f"🎯 Target: {expected_count} reviews to render")
            
            # 🚀 PERSISTENT BROWSER: 먼저 기존 브라우저 확인
            from services.persistent_browser_manager import browser_manager
            
            driver = browser_manager.get_browser(current_user_id)
            
            if driver:
                print(f"♻️ Reusing persistent browser for {current_user_id}")
                driver_is_persistent = True
            else:
                print(f"🆕 Creating new browser for {current_user_id} (no persistent browser)")
                driver = self._create_driver(headless=True, user_id=current_user_id)
                driver_is_persistent = False
            
            # Go to reviews page with "미등록" filter (hasReply=false)
            # 🚀 URL 파라미터로 미답글 리뷰만 필터링 (UI 조작보다 훨씬 안정적!)
            reviews_url = f'https://new.smartplace.naver.com/bizes/place/{place_id}/reviews?menu=visitor&hasReply=false'
            print(f"🔗 Opening: {reviews_url}")
            print(f"   ✅ Filter: hasReply=false (unreplied reviews only)")
            driver.get(reviews_url)
            time.sleep(3)
            
            # Handle popup
            try:
                popup_btn = driver.find_element(By.CSS_SELECTOR, "button.Modal_btn_confirm__uQZFR")
                if popup_btn.is_displayed():
                    driver.execute_script("arguments[0].click();", popup_btn)
                    time.sleep(1)
            except:
                pass
            
            # 🚀 URL 파라미터로 필터가 이미 적용됨 (hasReply=false)
            # UI 조작 불필요! 훨씬 빠르고 안정적
            print("✅ Filter applied via URL parameter (hasReply=false)")
            
            # 🚀 점진적 로딩 전략: 10개씩 렌더링하면서 찾기 (속도 향상!)
            print(f"🚀 Progressive loading: Searching in chunks of 10 reviews...")
            
            # 🔧 날짜에서 요일 제거 (비교 전) - 한 번만 실행
            date_clean = re.sub(r'\([^)]*\)', '', date).strip()
            author_prefix = author[:min(3, len(author))]
            print(f"🎯 Target: author='{author_prefix}...', date='{date_clean}'")
            
            scroll_count = 0
            max_scrolls = 20
            target_review = None
            batch_size = 10  # 10개씩 처리
            last_check_count = 0  # 마지막으로 확인한 리뷰 개수
            consecutive_no_load = 0  # 🔧 연속으로 새 리뷰가 로드되지 않은 횟수
            
            while scroll_count < max_scrolls and not target_review:
                # 현재 페이지의 모든 요소 가져오기
                all_lis = driver.find_elements(By.TAG_NAME, "li")
                
                # 유효한 리뷰만 필터링 (작성자 요소가 있는 것)
                valid_reviews = []
                for li in all_lis:
                    try:
                        li.find_element(By.CLASS_NAME, "pui__JiVbY3")
                        valid_reviews.append(li)
                    except:
                        continue
                
                current_count = len(valid_reviews)
                newly_loaded = current_count - last_check_count
                
                print(f"  📦 Batch {scroll_count + 1}: {current_count} total reviews ({newly_loaded} newly loaded)")
                
                # 🔧 연속 0개 카운트 업데이트
                if newly_loaded == 0:
                    consecutive_no_load += 1
                else:
                    consecutive_no_load = 0  # 리셋
                
                # 🔍 새로 로드된 리뷰에서만 검색 (효율적!)
                search_start_idx = max(0, last_check_count)
                search_reviews = valid_reviews[search_start_idx:]
                
                if search_reviews:
                    print(f"  🔍 Searching in reviews [{search_start_idx}:{current_count}]...")
                    
                    # 🎯 타겟 리뷰 찾기 (작성자 + 날짜 + 내용 매칭)
                    for idx, li in enumerate(search_reviews):
                        try:
                            # 작성자 가져오기
                            try:
                                li_author = li.find_element(By.CLASS_NAME, "pui__JiVbY3").text.strip()
                            except:
                                continue
                            
                            # 날짜 가져오기
                            li_date = ""
                            try:
                                d_elems = li.find_elements(By.CLASS_NAME, "pui__m7nkds")
                                for d in d_elems:
                                    if re.search(r'20\d{2}\.', d.text):
                                        li_date = d.text.strip()
                                        break
                            except:
                                continue
                            
                            # 🚀 작성자 + 날짜 매칭 (요일 제거, 작성자 부분 일치)
                            li_date_clean = re.sub(r'\([^)]*\)', '', li_date).strip()
                            
                            # 작성자 매칭 (앞 3글자) - author_prefix는 위에서 이미 정의됨
                            author_match = li_author.startswith(author_prefix)
                            date_match = li_date_clean == date_clean
                            
                            # 내용 매칭 (있으면)
                            content_match = True
                            if content and len(content) > 10:
                                try:
                                    li_content = li.find_element(By.CLASS_NAME, "pui__vn15t2").text.strip()
                                    content_match = content[:50] in li_content[:100]
                                except:
                                    content_match = True
                            
                            # 🎯 매칭 성공!
                            if author_match and date_match and content_match:
                                print(f"  ✅ Found at position {search_start_idx + idx}: '{li_author}' ({li_date_clean})")
                                target_review = li
                                break
                                
                        except Exception as e:
                            # 개별 리뷰 파싱 실패 시 계속 진행 (에러 방지)
                            continue
                    
                    if target_review:
                        print(f"🎉 Target review found after {scroll_count + 1} batches!")
                        break
                
                # 🚀 목표 개수에 도달했거나 더 이상 로드할 것이 없으면 중단
                if current_count >= expected_count:
                    print(f"  ℹ️ Reached expected count: {current_count} >= {expected_count}")
                    if not target_review:
                        print(f"  ⚠️ Target not found yet, searching all loaded reviews...")
                        # 전체 다시 검색 (혹시 놓친 것이 있을 수 있음)
                        break
                    else:
                        break
                
                # 🔧 FIX: expected_count를 고려하여 중단 결정
                # 연속 3번 새 리뷰가 없고, 스크롤을 충분히 시도했으면 중단
                if consecutive_no_load >= 3 and scroll_count >= 5:
                    if current_count < expected_count:
                        print(f"  ⚠️ Loaded only {current_count}/{expected_count}, but no more reviews available")
                    else:
                        print(f"  ℹ️ No new reviews loaded for {consecutive_no_load} attempts, stopping scroll")
                    break
                
                # 다음 배치를 위해 스크롤
                last_check_count = current_count
                driver.execute_script("window.scrollBy(0, 1500);")
                time.sleep(1.5)  # 🔧 1초 → 1.5초로 증가 (네이버 동적 로딩 대기)
                scroll_count += 1
            
            # 🔍 타겟을 못 찾았으면 전체 다시 검색 (안전장치)
            if not target_review:
                print(f"⚠️ Not found in progressive search, searching all {len(valid_reviews)} reviews...")
                
                # 맨 위로 스크롤
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                
                all_lis = driver.find_elements(By.TAG_NAME, "li")
                print(f"📋 Found {len(all_lis)} total elements on page")
                
                for li in all_lis:
                    try:
                        # 작성자 가져오기 (한국어, *, 영어 모두 처리)
                        try:
                            li_author = li.find_element(By.CLASS_NAME, "pui__JiVbY3").text.strip()
                        except:
                            continue
                        
                        # 날짜 가져오기
                        li_date = ""
                        try:
                            d_elems = li.find_elements(By.CLASS_NAME, "pui__m7nkds")
                            for d in d_elems:
                                if re.search(r'20\d{2}\.', d.text):
                                    li_date = d.text.strip()
                                    break
                        except:
                            continue
                        
                        # 🚀 작성자 + 날짜 매칭 (요일 제거) - 변수는 이미 위에서 정의됨
                        li_date_clean = re.sub(r'\([^)]*\)', '', li_date).strip()
                        
                        # 🚀 3중 매칭: 작성자(부분) + 날짜 + 내용(부분)
                        author_match = li_author.startswith(author_prefix)
                        date_match = li_date_clean == date_clean
                        
                        # 내용 매칭 (있으면)
                        content_match = True
                        if content and len(content) > 10:
                            try:
                                li_content = li.find_element(By.CLASS_NAME, "pui__vn15t2").text.strip()
                                content_match = content[:50] in li_content[:100]
                            except:
                                content_match = True  # 내용 없으면 패스
                        
                        if author_match and date_match and content_match:
                            print(f"✅ Found review (fallback): author='{li_author}' (starts with '{author_prefix}'), date='{li_date_clean}'")
                            target_review = li
                            break
                            
                    except:
                        continue
            
            if not target_review:
                # 에러 메시지 (date_clean, author_prefix는 이미 정의됨)
                print(f"❌ Could not find review!")
                print(f"   Looking for: author starts with '{author_prefix}', date='{date_clean}'")
                print(f"   Original: author='{author}', date='{date}'")
                print(f"⚠️ Debugging - first 5 reviews on page:")
                
                # 디버깅: 페이지의 모든 리뷰 출력
                for idx, li in enumerate(all_lis[:5]):
                    try:
                        debug_author = li.find_element(By.CLASS_NAME, "pui__JiVbY3").text.strip()
                        debug_date = ""
                        d_elems = li.find_elements(By.CLASS_NAME, "pui__m7nkds")
                        for d in d_elems:
                            if re.search(r'20\d{2}\.', d.text):
                                debug_date = d.text.strip()
                                break
                        debug_date_clean = re.sub(r'\([월화수목금토일]\)', '', debug_date).strip()
                        print(f"  [{idx}] Author: '{debug_author}', Date: '{debug_date}' (clean: '{debug_date_clean}')")
                    except:
                        pass
                
                raise Exception(f"Could not find review: author='{author_prefix}...', date='{date_clean}'")
            
            # Scroll to review
            print("📜 Scrolling to review...")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_review)
            time.sleep(1)
            
            # 🛡️ 답글이 이미 있는지 확인
            print("🔍 Checking if reply already exists...")
            try:
                existing_reply = target_review.find_element(By.CLASS_NAME, "pui__GbW8H7")
                if existing_reply:
                    print("⚠️ Reply already exists!")
                    raise Exception("이미 답글이 존재하는 리뷰입니다. 답글을 수정하려면 네이버에서 직접 수정해주세요.")
            except Exception as e:
                if "이미 답글이 존재" in str(e):
                    raise
                # 답글이 없으면 정상 (NoSuchElementException)
                print("✅ No existing reply, safe to proceed")
            
            # 🚀 CRITICAL: "답글 쓰기" 버튼 찾기 및 클릭
            print("🖱️  Finding '답글' button...")
            reply_btn = None
            
            # 여러 가지 방법으로 시도 (안정성 향상)
            try:
                # 방법 1: "답글" 텍스트 포함
                reply_btn = target_review.find_element(By.XPATH, ".//button[contains(., '답글')]")
                print("✅ Found by '답글' text")
            except:
                try:
                    # 방법 2: "답글 쓰기" 전체 텍스트
                    reply_btn = target_review.find_element(By.XPATH, ".//button[contains(., '답글 쓰기')]")
                    print("✅ Found by '답글 쓰기' text")
                except:
                    try:
                        # 방법 3: "답글달기" (띄어쓰기 없는 경우)
                        reply_btn = target_review.find_element(By.XPATH, ".//button[contains(., '답글달기')]")
                        print("✅ Found by '답글달기' text")
                    except:
                        print("❌ Could not find reply button")
                        raise Exception("답글 버튼을 찾을 수 없습니다. 이미 답글이 있거나 페이지 로딩이 완료되지 않았습니다.")
            
            # 버튼 클릭
            print("🖱️  Clicking reply button...")
            driver.execute_script("arguments[0].click();", reply_btn)
            time.sleep(2)
            print("✅ Reply form opened")
            
            # Fill textarea (실제 키 입력으로 React 이벤트 트리거)
            print("⌨️  Waiting for textarea...")
            textarea = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "textarea"))
            )
            
            # 🛡️ BMP 문자 필터링 (이모지 및 특수 문자 제거)
            def remove_non_bmp(text):
                """
                ChromeDriver가 지원하지 않는 BMP 밖의 문자 제거
                (이모지, 특수 유니코드 등)
                """
                # BMP 범위: U+0000 ~ U+FFFF
                return ''.join(c for c in text if ord(c) <= 0xFFFF)
            
            # 원본 텍스트 보관 (로깅용)
            original_reply_text = reply_text
            
            # 🔥 BMP 필터링 (에러 방지)
            reply_text_safe = remove_non_bmp(reply_text)
            
            # 필터링 결과 로깅
            if len(reply_text_safe) < len(original_reply_text):
                removed_chars = len(original_reply_text) - len(reply_text_safe)
                print(f"⚠️  Removed {removed_chars} non-BMP characters (emojis/special chars)")
            
            print(f"⌨️  Filling reply with send_keys: {reply_text_safe[:30]}...")
            
            # 🚀 STRATEGY: textarea에 focus를 주고 클릭한 다음 입력
            driver.execute_script("arguments[0].focus();", textarea)
            driver.execute_script("arguments[0].click();", textarea)
            time.sleep(0.3)
            
            textarea.clear()
            time.sleep(0.5)
            
            # 🚀 CRITICAL: send_keys()로 실제 키 입력 (React 이벤트 트리거)
            # 필터링된 텍스트 사용 (BMP만)
            textarea.send_keys(reply_text_safe)
            time.sleep(1)
            
            # 🔍 검증: 텍스트가 실제로 입력되었는지 확인
            actual_value = driver.execute_script("return arguments[0].value;", textarea)
            if len(actual_value) < 10:
                print(f"⚠️  send_keys failed (value: {len(actual_value)} chars)")
                print("   🔧 Retrying with enhanced JavaScript...")
                
                # 🚀 더 강력한 JavaScript 입력 (React 이벤트 확실하게 트리거)
                driver.execute_script("""
                    const textarea = arguments[0];
                    const text = arguments[1];
                    
                    // 값 설정
                    textarea.value = text;
                    
                    // React가 감지할 수 있도록 다양한 이벤트 트리거
                    textarea.dispatchEvent(new Event('focus', { bubbles: true }));
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                    textarea.dispatchEvent(new Event('change', { bubbles: true }));
                    textarea.dispatchEvent(new Event('blur', { bubbles: true }));
                    
                    // React 16+ 대응: nativeEvent descriptor 설정
                    const inputEvent = new InputEvent('input', {
                        data: text,
                        inputType: 'insertText',
                        bubbles: true,
                        cancelable: true
                    });
                    textarea.dispatchEvent(inputEvent);
                """, textarea, reply_text_safe)
                
                time.sleep(1)  # React 상태 업데이트 대기
                actual_value = driver.execute_script("return arguments[0].value;", textarea)
                print(f"   ✅ After enhanced JS: {len(actual_value)} chars")
                
                if len(actual_value) < 10:
                    raise Exception(f"Failed to fill textarea (value: {len(actual_value)} chars)")
            else:
                print(f"✅ Text input verified: {len(actual_value)} chars")
            
            # 🚀 target_review 내에서만 "등록" 찾기
            print("📤 Finding '등록' button in target review...")
            try:
                submit_btn = target_review.find_element(By.XPATH, ".//button[contains(text(), '등록')]")
                print("✅ Found '등록' in target review")
            except:
                print("⚠️ Not in target, searching all visible buttons...")
                all_btns = driver.find_elements(By.XPATH, "//button[contains(., '등록')]")
                visible = [b for b in all_btns if b.is_displayed()]
                submit_btn = visible[-1] if visible else None
                if not submit_btn:
                    raise Exception("No '등록' button found")
                print(f"✅ Found visible '등록' (index {len(visible)-1})")
            
            # 🔍 등록 전 최종 검증: textarea 값 재확인
            final_value = driver.execute_script("return arguments[0].value;", textarea)
            print(f"🔍 Final textarea check before submit: {len(final_value)} chars")
            if len(final_value) < 10:
                raise Exception(f"Textarea empty before submit! (value: {len(final_value)} chars)")
            
            # 🔍 등록 버튼 상태 확인
            is_disabled = submit_btn.get_attribute("disabled")
            is_aria_disabled = submit_btn.get_attribute("aria-disabled")
            if is_disabled or is_aria_disabled == "true":
                print(f"❌ Submit button is disabled! (disabled={is_disabled}, aria-disabled={is_aria_disabled})")
                raise Exception("등록 버튼이 비활성화 상태입니다")
            
            print("🖱️  Clicking '등록'...")
            driver.execute_script("arguments[0].click();", submit_btn)
            time.sleep(2)
            
            # 🔍 등록 후 에러 메시지 확인
            try:
                # 🔧 네이버 에러 메시지만 정확히 감지 (false positive 방지)
                error_selectors = [
                    "[role='alert']",
                    ".alert-error",
                    ".error-message",
                    "[class*='toast'][class*='error']",
                    "[class*='notification'][class*='error']"
                ]
                error_found = False
                for selector in error_selectors:
                    error_elems = driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in error_elems:
                        if elem.is_displayed():
                            text = elem.text.strip()
                            # 🔧 페이지 타이틀/헤더는 제외 (false positive 방지)
                            if text and len(text) > 5 and "스마트플레이스" not in text and "SmartPlace" not in text:
                                print(f"⚠️  Error message detected: {text[:100]}")
                                error_found = True
                if not error_found:
                    print("   ✅ No error messages detected")
            except:
                pass
            
            time.sleep(3)  # 총 5초 대기 (2초 + 3초)
            
            # 🚀 CRITICAL: 검증 - 실패 시 에러 발생
            print("🔍 Verifying reply...")
            time.sleep(4)  # 4초 대기 (네이버 렌더링 + DOM 업데이트)
            
            reply_verified = False
            
            # 🔧 FIX: 여러 번 재시도 (네이버 렌더링이 느릴 수 있음)
            max_retry = 3
            for retry in range(max_retry):
                try:
                    if retry > 0:
                        print(f"   🔄 Verification retry {retry}/{max_retry-1}...")
                        time.sleep(2)  # 재시도 시 추가 대기
                    
                    # 작성자+날짜로 다시 찾기 (이미 위에서 정의된 변수 사용)
                    
                    all_lis = driver.find_elements(By.TAG_NAME, "li")
                    for li in all_lis:
                        try:
                            li_author = li.find_element(By.CLASS_NAME, "pui__JiVbY3").text.strip()
                            if not li_author.startswith(author_prefix):
                                continue
                            
                            li_date = ""
                            d_elems = li.find_elements(By.CLASS_NAME, "pui__m7nkds")
                            for d in d_elems:
                                if re.search(r'20\d{2}\.', d.text):
                                    li_date = d.text.strip()
                                    break
                            
                            li_date_clean = re.sub(r'\([^)]*\)', '', li_date).strip()
                            
                            if li_date_clean == date_clean:
                                # 이 리뷰에서 답글 요소 찾기
                                reply_elem = li.find_element(By.CLASS_NAME, "pui__GbW8H7")
                                reply_preview = reply_elem.text[:50]
                                print(f"✅ Reply verified: {reply_preview}...")
                                reply_verified = True
                                break
                        except:
                            continue
                    
                    if reply_verified:
                        break  # 성공하면 재시도 중단
                        
                except Exception as e:
                    if retry == max_retry - 1:
                        print(f"❌ Verification error: {e}")
            
            # 🚨 CRITICAL: Verification 실패 = 답글 등록 실패
            if not reply_verified:
                # 디버깅: 페이지 상태 확인
                print("🔍 Debug: Checking page state...")
                try:
                    current_url = driver.current_url
                    print(f"   Current URL: {current_url}")
                    # 에러 메시지가 있는지 다시 확인
                    error_elems = driver.find_elements(By.CSS_SELECTOR, "[class*='error'], [class*='alert'], [role='alert']")
                    if error_elems:
                        for elem in error_elems:
                            if elem.is_displayed():
                                print(f"   ⚠️ Error on page: {elem.text[:100]}")
                except:
                    pass
                raise Exception("Reply verification failed - 답글이 실제로 게시되지 않았습니다")
            
            if reply_verified:
                print(f"✅ Reply posted and verified successfully!")
                return {
                    'success': True,
                    'message': 'Reply posted and verified successfully'
                }
            else:
                print(f"⚠️ Reply posted (verification skipped due to DOM changes)")
                return {
                    'success': True,
                    'message': 'Reply posted successfully (verification skipped)',
                    'verified': False
                }
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error posting reply: {error_msg}")
            logger.error(f"Error posting reply: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Error posting reply: {error_msg}")
        
        finally:
            # 🚀 PERSISTENT BROWSER: persistent browser는 닫지 않음!
            if driver and not driver_is_persistent:
                try:
                    print("🔄 Closing temporary browser...")
                    driver.quit()
                    print("✅ Temporary browser closed")
                except Exception as e:
                    print(f"⚠️ Error closing driver: {e}")
            elif driver and driver_is_persistent:
                print("♻️ Keeping persistent browser alive")
    
    def post_reply(self, place_id: str, review_id: str, reply_text: str) -> Dict:
        """Post a reply to a review in Smartplace Center"""
        driver = None
        driver_is_persistent = False
        current_user_id = self.active_user_id
        
        try:
            print(f"💬 Posting reply to review: {review_id} for user: {current_user_id}")
            logger.info(f"💬 Posting reply to review: {review_id}")
            
            # 🚀 PERSISTENT BROWSER: 먼저 기존 브라우저 확인
            from services.persistent_browser_manager import browser_manager
            
            driver = browser_manager.get_browser(current_user_id)
            
            if driver:
                print(f"♻️ Reusing persistent browser for {current_user_id}")
                driver_is_persistent = True
            else:
                print(f"🆕 Creating new browser for {current_user_id} (no persistent browser)")
                driver = self._create_driver(headless=True, user_id=current_user_id)
                driver_is_persistent = False
            
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
            # 🚀 PERSISTENT BROWSER: persistent browser는 닫지 않음!
            if driver and not driver_is_persistent:
                driver.quit()
                print("🔒 Closed temporary browser")
            elif driver and driver_is_persistent:
                print("♻️ Keeping persistent browser alive")
    
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
            current_user_id = self.active_user_id
            
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            
            # 🚀 PERSISTENT BROWSER: 브라우저 종료
            from services.persistent_browser_manager import browser_manager
            browser_manager.remove_browser(current_user_id)
            print(f"🗑️ Persistent browser removed for {current_user_id}")
            
            # 🚀 Clear cache on logout (user별로 클리어!)
            if current_user_id in self._places_cache:
                del self._places_cache[current_user_id]
            if current_user_id in self._places_cache_time:
                del self._places_cache_time[current_user_id]
            # Reviews cache는 place_id별로 관리되므로 전체 클리어 (추후 개선 가능)
            self._reviews_cache = {}  # Clear reviews cache too
            self._loading_progress = {}  # Clear progress too
            print(f"🗑️ Cache cleared for user {current_user_id}")
            
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
