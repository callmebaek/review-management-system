"""
Naver Smart Place Center Automation using Playwright
⚠️ 주의: 네이버는 공식 리뷰 관리 API를 제공하지 않습니다.
이 모듈은 개인 사용 목적으로만 사용하시기 바랍니다.
"""

from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
import json
import os
import time
from typing import List, Dict, Optional
from datetime import datetime
from config import settings
from fastapi import HTTPException
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Thread executor for running sync Playwright in async context
executor = ThreadPoolExecutor(max_workers=4)


class NaverPlaceAutomation:
    """Naver Smart Place Center automation service"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.session_file = os.path.join(settings.data_dir, "naver_sessions", "session.json")
        os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
    
    async def _init_browser(self, headless: bool = True):
        """Initialize Playwright browser"""
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=headless)
            
            # Load session if exists
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                self.context = await self.browser.new_context(
                    storage_state=session_data
                )
            else:
                self.context = await self.browser.new_context()
    
    async def _close_browser(self):
        """Close browser"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        self.browser = None
        self.context = None
    
    async def _save_session(self):
        """Save browser session (cookies, localStorage, etc.)"""
        if self.context:
            session_data = await self.context.storage_state()
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
    
    async def login(self, username: str, password: str, headless: bool = False) -> Dict:
        """
        Login to Naver Smart Place Center
        
        Args:
            username: Naver username
            password: Naver password
            headless: Run in headless mode (False for debugging)
        
        Returns:
            Dict with login status
        """
        try:
            await self._init_browser(headless=headless)
            page = await self.context.new_page()
            
            # Navigate to Naver login
            await page.goto('https://nid.naver.com/nidlogin.login')
            
            # Fill login form
            await page.fill('#id', username)
            await page.fill('#pw', password)
            
            # Click login button
            await page.click('.btn_login')
            
            # Wait for login to complete
            try:
                # Wait for either success or failure
                await page.wait_for_url('https://www.naver.com/', timeout=10000)
                
                # Save session
                await self._save_session()
                
                await page.close()
                return {
                    'success': True,
                    'message': 'Successfully logged in to Naver'
                }
            except Exception as e:
                # Check if login failed
                error_message = await page.locator('.error_message').text_content() if await page.locator('.error_message').count() > 0 else str(e)
                await page.close()
                return {
                    'success': False,
                    'message': f'Login failed: {error_message}'
                }
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")
        finally:
            await self._close_browser()
    
    async def check_login_status(self) -> Dict:
        """
        Check if logged in to Naver
        
        Returns:
            Dict with login status
        """
        try:
            if not os.path.exists(self.session_file):
                return {
                    'logged_in': False,
                    'message': 'No session found. Please login first.'
                }
            
            await self._init_browser(headless=True)
            page = await self.context.new_page()
            
            # Try to access Smart Place Center
            await page.goto('https://new-m.place.naver.com/my/')
            
            # Check if redirected to login page
            if 'nid.naver.com' in page.url:
                await page.close()
                return {
                    'logged_in': False,
                    'message': 'Session expired. Please login again.'
                }
            
            await page.close()
            return {
                'logged_in': True,
                'message': 'Logged in to Naver'
            }
            
        except Exception as e:
            return {
                'logged_in': False,
                'message': f'Error checking login status: {str(e)}'
            }
        finally:
            await self._close_browser()
    
    async def get_places(self) -> List[Dict]:
        """
        Get list of places registered in Smart Place Center
        
        Returns:
            List of place dictionaries
        """
        try:
            await self._init_browser(headless=True)
            page = await self.context.new_page()
            
            # Navigate to Smart Place Center
            await page.goto('https://new-m.place.naver.com/my/')
            
            # Wait for places to load
            await page.wait_for_selector('.place_item', timeout=5000)
            
            # Extract place information
            places = []
            place_elements = await page.query_selector_all('.place_item')
            
            for element in place_elements:
                try:
                    name = await element.query_selector('.place_name')
                    name_text = await name.text_content() if name else ''
                    
                    place_id = await element.get_attribute('data-place-id')
                    
                    places.append({
                        'place_id': place_id,
                        'name': name_text.strip(),
                        'url': f'https://new-m.place.naver.com/my/place/{place_id}'
                    })
                except Exception as e:
                    print(f"Error extracting place: {e}")
                    continue
            
            await page.close()
            return places
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching places: {str(e)}")
        finally:
            await self._close_browser()
    
    async def get_reviews(self, place_id: str) -> List[Dict]:
        """
        Get reviews for a specific place
        
        Args:
            place_id: Naver place ID
        
        Returns:
            List of review dictionaries
        """
        try:
            await self._init_browser(headless=True)
            page = await self.context.new_page()
            
            # Navigate to reviews page
            reviews_url = f'https://new-m.place.naver.com/my/place/{place_id}/review'
            await page.goto(reviews_url)
            
            # Wait for reviews to load
            await page.wait_for_selector('.review_item', timeout=5000)
            
            # Extract review information
            reviews = []
            review_elements = await page.query_selector_all('.review_item')
            
            for element in review_elements:
                try:
                    # Extract review details
                    author_elem = await element.query_selector('.reviewer_name')
                    author = await author_elem.text_content() if author_elem else 'Unknown'
                    
                    date_elem = await element.query_selector('.review_date')
                    date_text = await date_elem.text_content() if date_elem else ''
                    
                    rating_elem = await element.query_selector('.rating')
                    rating = await rating_elem.get_attribute('data-rating') if rating_elem else '0'
                    
                    content_elem = await element.query_selector('.review_content')
                    content = await content_elem.text_content() if content_elem else ''
                    
                    # Check if reply exists
                    reply_elem = await element.query_selector('.owner_reply')
                    has_reply = reply_elem is not None
                    reply_text = await reply_elem.text_content() if has_reply else None
                    
                    review_id = await element.get_attribute('data-review-id')
                    
                    reviews.append({
                        'review_id': review_id,
                        'author': author.strip(),
                        'date': date_text.strip(),
                        'rating': int(rating) if rating.isdigit() else 0,
                        'content': content.strip(),
                        'has_reply': has_reply,
                        'reply': reply_text.strip() if reply_text else None
                    })
                except Exception as e:
                    print(f"Error extracting review: {e}")
                    continue
            
            await page.close()
            return reviews
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching reviews: {str(e)}")
        finally:
            await self._close_browser()
    
    async def post_reply(self, place_id: str, review_id: str, reply_text: str) -> Dict:
        """
        Post a reply to a review
        
        Args:
            place_id: Naver place ID
            review_id: Review ID
            reply_text: Reply text to post
        
        Returns:
            Dict with success status
        """
        try:
            await self._init_browser(headless=True)
            page = await self.context.new_page()
            
            # Navigate to reviews page
            reviews_url = f'https://new-m.place.naver.com/my/place/{place_id}/review'
            await page.goto(reviews_url)
            
            # Find the specific review
            review_elem = await page.query_selector(f'[data-review-id="{review_id}"]')
            if not review_elem:
                raise HTTPException(status_code=404, detail=f"Review {review_id} not found")
            
            # Click reply button
            reply_button = await review_elem.query_selector('.reply_button')
            if reply_button:
                await reply_button.click()
                await page.wait_for_timeout(1000)
            
            # Fill reply textarea
            reply_textarea = await review_elem.query_selector('.reply_textarea')
            if not reply_textarea:
                raise HTTPException(status_code=400, detail="Reply textarea not found")
            
            await reply_textarea.fill(reply_text)
            
            # Click submit button
            submit_button = await review_elem.query_selector('.submit_reply')
            if submit_button:
                await submit_button.click()
                
                # Wait for success confirmation
                await page.wait_for_timeout(2000)
            
            # Apply rate limiting
            await asyncio.sleep(settings.naver_rate_limit_delay)
            
            await page.close()
            return {
                'success': True,
                'message': 'Reply posted successfully',
                'review_id': review_id
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error posting reply: {str(e)}")
        finally:
            await self._close_browser()
    
    async def logout(self) -> Dict:
        """
        Logout and clear session
        
        Returns:
            Dict with logout status
        """
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            
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
naver_automation = NaverPlaceAutomation()



