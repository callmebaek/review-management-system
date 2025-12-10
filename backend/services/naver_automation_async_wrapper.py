"""
Async wrapper for sync Naver automation (for FastAPI compatibility)
"""
import asyncio
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
from services.naver_automation_sync import naver_automation_sync
from typing import Dict, List
import logging
import traceback

logger = logging.getLogger(__name__)

# Thread executor for running sync code in async context
executor = ThreadPoolExecutor(max_workers=4)


class NaverAutomationAsyncWrapper:
    """Async wrapper around sync Naver automation"""
    
    def __init__(self):
        self.sync_automation = naver_automation_sync
    
    async def login(self, username: str, password: str) -> Dict:
        """Async wrapper for login"""
        try:
            logger.info(f"🔄 Starting Naver login for user: {username}")
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                self.sync_automation.login,
                username,
                password
            )
            logger.info(f"✅ Login result: {result}")
            return result
        except Exception as e:
            logger.error(f"❌ Login error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'message': f'Login error: {str(e)}'
            }
    
    async def check_login_status(self) -> Dict:
        """Async wrapper for check_login_status"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            executor,
            self.sync_automation.check_login_status
        )
    
    async def get_places(self) -> List[Dict]:
        """Async wrapper for get_places"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            executor,
            self.sync_automation.get_places
        )
    
    async def get_reviews(self, place_id: str) -> List[Dict]:
        """Async wrapper for get_reviews"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            executor,
            self.sync_automation.get_reviews,
            place_id
        )
    
    async def post_reply(self, place_id: str, review_id: str, reply_text: str) -> Dict:
        """Async wrapper for post_reply"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            executor,
            self.sync_automation.post_reply,
            place_id,
            review_id,
            reply_text
        )
    
    async def logout(self) -> Dict:
        """Async wrapper for logout"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            executor,
            self.sync_automation.logout
        )


# Create singleton instance
naver_automation = NaverAutomationAsyncWrapper()

