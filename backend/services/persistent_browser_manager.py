"""
Persistent Browser Manager

OAuth 로그인 후 브라우저를 백그라운드에 유지하여 세션 관리
- 사용자별로 브라우저 1개씩 유지
- 30분 idle 시 자동 종료
- 재로그인 시 새 브라우저 생성
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os

logger = logging.getLogger(__name__)


class PersistentBrowserManager:
    """백그라운드 브라우저 관리자 (싱글톤)"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        
        # 사용자별 브라우저 저장
        # {user_id: {'driver': WebDriver, 'last_used': datetime, 'user_agent': str}}
        self._browsers: Dict[str, Dict] = {}
        
        # Lock for thread safety
        self._browser_lock = threading.Lock()
        
        # Idle timeout (30분)
        self._idle_timeout = timedelta(minutes=30)
        
        # Cleanup 스레드 시작
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_idle_browsers,
            daemon=True
        )
        self._cleanup_thread.start()
        
        logger.info("✅ PersistentBrowserManager initialized")
        print("✅ PersistentBrowserManager initialized")
    
    def register_browser(self, user_id: str, driver: webdriver.Chrome, user_agent: str = None):
        """
        OAuth 로그인 완료 후 브라우저 등록
        
        Args:
            user_id: 사용자 ID (네이버 계정 ID)
            driver: Selenium WebDriver 인스턴스
            user_agent: User-Agent 문자열
        """
        with self._browser_lock:
            # 기존 브라우저가 있으면 종료
            if user_id in self._browsers:
                old_driver = self._browsers[user_id]['driver']
                try:
                    old_driver.quit()
                    print(f"🔄 Closed old browser for {user_id}")
                except:
                    pass
            
            # 새 브라우저 등록
            self._browsers[user_id] = {
                'driver': driver,
                'last_used': datetime.now(),
                'user_agent': user_agent or driver.execute_script("return navigator.userAgent"),
                'created_at': datetime.now()
            }
            
            logger.info(f"✅ Browser registered for user: {user_id}")
            print(f"✅ Browser registered for user: {user_id}")
    
    def get_browser(self, user_id: str) -> Optional[webdriver.Chrome]:
        """
        사용자의 브라우저 가져오기
        
        Returns:
            WebDriver 또는 None (브라우저 없으면)
        """
        with self._browser_lock:
            if user_id in self._browsers:
                browser_info = self._browsers[user_id]
                
                # 브라우저가 살아있는지 확인
                try:
                    # Ping test
                    browser_info['driver'].current_url
                    
                    # 마지막 사용 시간 업데이트
                    browser_info['last_used'] = datetime.now()
                    
                    logger.info(f"♻️ Reusing browser for user: {user_id}")
                    print(f"♻️ Reusing persistent browser for user: {user_id}")
                    
                    return browser_info['driver']
                except:
                    # 브라우저가 죽었으면 제거
                    logger.warning(f"💀 Browser dead for user: {user_id}")
                    print(f"💀 Browser dead for user: {user_id}, removing...")
                    del self._browsers[user_id]
                    return None
            
            return None
    
    def remove_browser(self, user_id: str):
        """브라우저 제거 및 종료"""
        with self._browser_lock:
            if user_id in self._browsers:
                driver = self._browsers[user_id]['driver']
                try:
                    driver.quit()
                    print(f"🔒 Browser closed for user: {user_id}")
                except:
                    pass
                
                del self._browsers[user_id]
                logger.info(f"🗑️ Browser removed for user: {user_id}")
    
    def get_active_browsers_count(self) -> int:
        """현재 활성 브라우저 수"""
        with self._browser_lock:
            return len(self._browsers)
    
    def get_browser_info(self, user_id: str) -> Optional[Dict]:
        """브라우저 정보 조회 (디버깅용)"""
        with self._browser_lock:
            if user_id in self._browsers:
                info = self._browsers[user_id]
                return {
                    'user_id': user_id,
                    'last_used': info['last_used'].isoformat(),
                    'created_at': info['created_at'].isoformat(),
                    'idle_seconds': (datetime.now() - info['last_used']).total_seconds(),
                    'user_agent': info['user_agent'][:80]
                }
            return None
    
    def _cleanup_idle_browsers(self):
        """백그라운드 스레드: idle 브라우저 정리"""
        logger.info("🧹 Cleanup thread started")
        
        while True:
            try:
                time.sleep(60)  # 1분마다 체크
                
                with self._browser_lock:
                    now = datetime.now()
                    to_remove = []
                    
                    for user_id, info in self._browsers.items():
                        idle_time = now - info['last_used']
                        
                        if idle_time > self._idle_timeout:
                            idle_minutes = int(idle_time.total_seconds() / 60)
                            logger.info(f"🧹 Closing idle browser: {user_id} (idle: {idle_minutes}m)")
                            print(f"🧹 Closing idle browser: {user_id} (idle: {idle_minutes}분)")
                            
                            try:
                                info['driver'].quit()
                            except:
                                pass
                            
                            to_remove.append(user_id)
                    
                    for user_id in to_remove:
                        del self._browsers[user_id]
                    
                    if to_remove:
                        logger.info(f"🧹 Cleaned up {len(to_remove)} idle browsers")
                
            except Exception as e:
                logger.error(f"❌ Cleanup error: {e}")


# 싱글톤 인스턴스
browser_manager = PersistentBrowserManager()






