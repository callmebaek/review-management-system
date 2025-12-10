"""
Naver Smart Place Center Automation using Playwright (SYNC API for Python 3.13 compatibility)
⚠️ 주의: 네이버는 공식 리뷰 관리 API를 제공하지 않습니다.
이 모듈은 개인 사용 목적으로만 사용하시기 바랍니다.
"""

from playwright.sync_api import sync_playwright, Browser, BrowserContext
import json
import os
import time
import logging
import traceback
from typing import List, Dict
from config import settings
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class NaverPlaceAutomationSync:
    """Naver Smart Place Center automation service using sync API"""
    
    def __init__(self):
        self.session_file = os.path.join(settings.data_dir, "naver_sessions", "session.json")
        os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
    
    def _run_with_browser(self, func, headless=True):
        """Run a function with browser context"""
        try:
            logger.info("🚀 Starting Playwright...")
            with sync_playwright() as p:
                logger.info("🌐 Launching Chromium browser...")
                browser = p.chromium.launch(headless=headless)
                logger.info("✅ Browser launched")
                
                # Load session if exists
                if os.path.exists(self.session_file):
                    with open(self.session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    context = browser.new_context(storage_state=session_data)
                else:
                    context = browser.new_context()
                
                try:
                    result = func(context)
                    return result
                finally:
                    context.close()
                    browser.close()
        except Exception as e:
            logger.error(f"❌ Browser error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _save_session(self, context: BrowserContext):
        """Save browser session"""
        session_data = context.storage_state()
        with open(self.session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
    
    def login(self, username: str, password: str) -> Dict:
        """Login to Naver Smart Place Center"""
        def _login(context):
            page = context.new_page()
            
            try:
                logger.info("📄 Opening Naver login page...")
                # Navigate to Naver login
                page.goto('https://nid.naver.com/nidlogin.login', timeout=30000)
                logger.info("✅ Page loaded")
                
                # Fill login form
                page.fill('#id', username)
                page.fill('#pw', password)
                
                # Click login button
                page.click('.btn_login')
                
                # Wait for login to complete
                try:
                    page.wait_for_url('https://www.naver.com/', timeout=10000)
                    
                    # Save session
                    self._save_session(context)
                    
                    return {
                        'success': True,
                        'message': 'Successfully logged in to Naver'
                    }
                except Exception as e:
                    # Check if login failed
                    error_elem = page.query_selector('.error_message')
                    error_message = error_elem.text_content() if error_elem else str(e)
                    return {
                        'success': False,
                        'message': f'Login failed: {error_message}'
                    }
            finally:
                page.close()
        
        try:
            return self._run_with_browser(_login, headless=True)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")
    
    def check_login_status(self) -> Dict:
        """Check if logged in to Naver"""
        if not os.path.exists(self.session_file):
            return {
                'logged_in': False,
                'message': 'No session found. Please login first.'
            }
        
        def _check(context):
            page = context.new_page()
            
            try:
                # Try to access Smart Place Center
                page.goto('https://new-m.place.naver.com/my/', timeout=30000)
                
                # Check if redirected to login page
                if 'nid.naver.com' in page.url:
                    return {
                        'logged_in': False,
                        'message': 'Session expired. Please login again.'
                    }
                
                return {
                    'logged_in': True,
                    'message': 'Logged in to Naver'
                }
            finally:
                page.close()
        
        try:
            return self._run_with_browser(_check)
        except Exception as e:
            return {
                'logged_in': False,
                'message': f'Error checking login status: {str(e)}'
            }
    
    def get_places(self) -> List[Dict]:
        """Get list of places in Smart Place Center"""
        def _get_places(context):
            page = context.new_page()
            
            try:
                # Navigate to Smart Place Center
                page.goto('https://new-m.place.naver.com/my/', timeout=30000)
                
                # Wait for places to load
                page.wait_for_selector('.place_item', timeout=5000)
                
                # Extract place information
                places = []
                place_elements = page.query_selector_all('.place_item')
                
                for element in place_elements:
                    try:
                        name_elem = element.query_selector('.place_name')
                        name = name_elem.text_content() if name_elem else ''
                        
                        place_id = element.get_attribute('data-place-id')
                        
                        places.append({
                            'place_id': place_id,
                            'name': name.strip(),
                            'url': f'https://new-m.place.naver.com/my/place/{place_id}'
                        })
                    except Exception as e:
                        print(f"Error extracting place: {e}")
                        continue
                
                return places
            finally:
                page.close()
        
        try:
            return self._run_with_browser(_get_places)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching places: {str(e)}")
    
    def get_reviews(self, place_id: str) -> List[Dict]:
        """Get reviews for a specific place"""
        def _get_reviews(context):
            page = context.new_page()
            
            try:
                # Navigate to reviews page
                reviews_url = f'https://new-m.place.naver.com/my/place/{place_id}/review'
                page.goto(reviews_url, timeout=30000)
                
                # Wait for reviews to load
                page.wait_for_selector('.review_item', timeout=5000)
                
                # Extract review information
                reviews = []
                review_elements = page.query_selector_all('.review_item')
                
                for element in review_elements:
                    try:
                        author_elem = element.query_selector('.reviewer_name')
                        author = author_elem.text_content() if author_elem else 'Unknown'
                        
                        date_elem = element.query_selector('.review_date')
                        date_text = date_elem.text_content() if date_elem else ''
                        
                        rating_elem = element.query_selector('.rating')
                        rating = rating_elem.get_attribute('data-rating') if rating_elem else '0'
                        
                        content_elem = element.query_selector('.review_content')
                        content = content_elem.text_content() if content_elem else ''
                        
                        reply_elem = element.query_selector('.owner_reply')
                        has_reply = reply_elem is not None
                        reply_text = reply_elem.text_content() if has_reply else None
                        
                        review_id = element.get_attribute('data-review-id')
                        
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
                
                return reviews
            finally:
                page.close()
        
        try:
            return self._run_with_browser(_get_reviews)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching reviews: {str(e)}")
    
    def post_reply(self, place_id: str, review_id: str, reply_text: str) -> Dict:
        """Post a reply to a review"""
        def _post_reply(context):
            page = context.new_page()
            
            try:
                # Navigate to reviews page
                reviews_url = f'https://new-m.place.naver.com/my/place/{place_id}/review'
                page.goto(reviews_url, timeout=30000)
                
                # Find the specific review
                review_elem = page.query_selector(f'[data-review-id="{review_id}"]')
                if not review_elem:
                    raise HTTPException(status_code=404, detail=f"Review {review_id} not found")
                
                # Click reply button
                reply_button = review_elem.query_selector('.reply_button')
                if reply_button:
                    reply_button.click()
                    time.sleep(1)
                
                # Fill reply textarea
                reply_textarea = review_elem.query_selector('.reply_textarea')
                if not reply_textarea:
                    raise HTTPException(status_code=400, detail="Reply textarea not found")
                
                reply_textarea.fill(reply_text)
                
                # Click submit button
                submit_button = review_elem.query_selector('.submit_reply')
                if submit_button:
                    submit_button.click()
                    time.sleep(2)
                
                # Apply rate limiting
                time.sleep(settings.naver_rate_limit_delay)
                
                return {
                    'success': True,
                    'message': 'Reply posted successfully',
                    'review_id': review_id
                }
            finally:
                page.close()
        
        try:
            return self._run_with_browser(_post_reply)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error posting reply: {str(e)}")
    
    def logout(self) -> Dict:
        """Logout and clear session"""
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
naver_automation_sync = NaverPlaceAutomationSync()

