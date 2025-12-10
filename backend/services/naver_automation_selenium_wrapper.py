"""
Async wrapper for Selenium Naver automation
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from services.naver_automation_selenium import naver_automation_selenium
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

# Thread executor
executor = ThreadPoolExecutor(max_workers=1)  # Reduced to 1 to prevent concurrent browser sessions

# Semaphore to ensure only one Selenium operation at a time
_selenium_lock = asyncio.Lock()


class NaverAutomationSeleniumWrapper:
    """Async wrapper for Selenium automation"""
    
    def __init__(self):
        self.selenium_automation = naver_automation_selenium
    
    async def login(self, username: str, password: str) -> Dict:
        """Async wrapper for login"""
        async with _selenium_lock:  # Ensure only one browser operation at a time
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                executor,
                self.selenium_automation.login,
                username,
                password
            )
    
    async def check_login_status(self) -> Dict:
        """Async wrapper for check_login_status (no lock needed - file-based check)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            executor,
            self.selenium_automation.check_login_status
        )
    
    async def get_places(self) -> List[Dict]:
        """Async wrapper for get_places"""
        async with _selenium_lock:  # Ensure only one browser operation at a time
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                executor,
                self.selenium_automation.get_places
            )
    
    async def get_reviews(self, place_id: str, page: int = 1, page_size: int = 20, filter_type: str = 'all', load_count: int = 300) -> List[Dict]:
        """Async wrapper for get_reviews (user-specified load count)"""
        async with _selenium_lock:  # Ensure only one browser operation at a time
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                executor,
                self.selenium_automation.get_reviews,
                place_id,
                page,
                page_size,
                filter_type,
                load_count
            )
    
    async def post_reply(self, place_id: str, review_id: str, reply_text: str) -> Dict:
        """Async wrapper for post_reply"""
        async with _selenium_lock:  # Ensure only one browser operation at a time
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                executor,
                self.selenium_automation.post_reply,
                place_id,
                review_id,
                reply_text
            )
    
    async def get_loading_progress(self, place_id: str) -> Dict:
        """Async wrapper for get_loading_progress (no lock needed - memory read)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            executor,
            self.selenium_automation.get_loading_progress,
            place_id
        )
    
    async def logout(self) -> Dict:
        """Async wrapper for logout"""
        async with _selenium_lock:  # Ensure only one browser operation at a time
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                executor,
                self.selenium_automation.logout
            )


# Create singleton instance
naver_automation = NaverAutomationSeleniumWrapper()

