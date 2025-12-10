"""
Mock Naver Place Service for testing without actual automation
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MockNaverService:
    """Mock implementation of Naver Place service for testing"""
    
    def __init__(self):
        self.logged_in = False
        self.mock_places = self._create_mock_places()
        self.mock_reviews = self._create_mock_reviews()
        logger.info("🎭 Mock Naver Service initialized")
    
    def _create_mock_places(self) -> List[Dict]:
        """Create mock Naver places"""
        return [
            {
                'place_id': 'naver-place-001',
                'name': '강남 카페 (네이버)',
                'url': 'https://place.naver.com/mock/001',
                'address': '서울 강남구 테헤란로 123',
                'category': '카페'
            },
            {
                'place_id': 'naver-place-002',
                'name': '홍대 레스토랑 (네이버)',
                'url': 'https://place.naver.com/mock/002',
                'address': '서울 마포구 양화로 456',
                'category': '레스토랑'
            },
            {
                'place_id': 'naver-place-003',
                'name': '판교 베이커리 (네이버)',
                'url': 'https://place.naver.com/mock/003',
                'address': '경기 성남시 분당구 판교역로 789',
                'category': '베이커리'
            }
        ]
    
    def _create_mock_reviews(self) -> Dict[str, List[Dict]]:
        """Create mock reviews for each place"""
        reviews_by_place = {}
        
        # Reviews for place 001 (강남 카페)
        reviews_by_place['naver-place-001'] = [
            {
                'review_id': 'naver-review-001-001',
                'author': '네이버유저123',
                'date': (datetime.now() - timedelta(days=1)).strftime('%Y.%m.%d'),
                'rating': 5,
                'content': '커피 맛이 정말 좋아요! 인테리어도 감각적이고 직원분들도 친절하세요.',
                'has_reply': False,
                'reply': None
            },
            {
                'review_id': 'naver-review-001-002',
                'author': '맛집탐험가',
                'date': (datetime.now() - timedelta(days=3)).strftime('%Y.%m.%d'),
                'rating': 4,
                'content': '아메리카노 맛있었어요. 다만 주말엔 사람이 너무 많아요.',
                'has_reply': True,
                'reply': '방문 감사합니다! 주말 혼잡 시간대 개선을 위해 노력하겠습니다.'
            },
            {
                'review_id': 'naver-review-001-003',
                'author': '카페마니아',
                'date': (datetime.now() - timedelta(days=5)).strftime('%Y.%m.%d'),
                'rating': 3,
                'content': '그냥 평범한 카페입니다. 특별한 건 없네요.',
                'has_reply': False,
                'reply': None
            },
            {
                'review_id': 'naver-review-001-004',
                'author': '커피러버',
                'date': (datetime.now() - timedelta(days=7)).strftime('%Y.%m.%d'),
                'rating': 5,
                'content': '라떼 아트가 예쁘고 맛도 좋아요. 자주 갈 것 같아요!',
                'has_reply': False,
                'reply': None
            }
        ]
        
        # Reviews for place 002 (홍대 레스토랑)
        reviews_by_place['naver-place-002'] = [
            {
                'review_id': 'naver-review-002-001',
                'author': '맛집헌터',
                'date': (datetime.now() - timedelta(hours=18)).strftime('%Y.%m.%d'),
                'rating': 5,
                'content': '음식 맛이 훌륭해요! 분위기도 좋고 데이트 장소로 최고입니다.',
                'has_reply': False,
                'reply': None
            },
            {
                'review_id': 'naver-review-002-002',
                'author': '홍대러',
                'date': (datetime.now() - timedelta(days=2)).strftime('%Y.%m.%d'),
                'rating': 2,
                'content': '음식은 괜찮은데 서비스가 너무 느려요. 주문하고 30분 넘게 기다렸어요.',
                'has_reply': False,
                'reply': None
            },
            {
                'review_id': 'naver-review-002-003',
                'author': '외식좋아',
                'date': (datetime.now() - timedelta(days=4)).strftime('%Y.%m.%d'),
                'rating': 4,
                'content': '파스타 맛있었습니다. 가격은 조금 있는 편이지만 품질이 좋아요.',
                'has_reply': True,
                'reply': '좋은 평가 감사합니다! 항상 최고의 맛을 위해 노력하겠습니다.'
            }
        ]
        
        # Reviews for place 003 (판교 베이커리)
        reviews_by_place['naver-place-003'] = [
            {
                'review_id': 'naver-review-003-001',
                'author': '빵순이',
                'date': (datetime.now() - timedelta(hours=10)).strftime('%Y.%m.%d'),
                'rating': 5,
                'content': '크루아상이 정말 바삭하고 맛있어요! 매일 사먹고 싶을 정도예요.',
                'has_reply': False,
                'reply': None
            },
            {
                'review_id': 'naver-review-003-002',
                'author': '판교주민',
                'date': (datetime.now() - timedelta(days=2)).strftime('%Y.%m.%d'),
                'rating': 5,
                'content': '신선한 빵과 친절한 서비스! 판교 최고의 베이커리입니다.',
                'has_reply': True,
                'reply': '항상 이용해주셔서 감사합니다! 신선한 빵으로 보답하겠습니다.'
            },
            {
                'review_id': 'naver-review-003-003',
                'author': '베이커리마니아',
                'date': (datetime.now() - timedelta(days=3)).strftime('%Y.%m.%d'),
                'rating': 4,
                'content': '빵 맛은 좋은데 가격이 좀 비싸요. 그래도 품질은 보장됩니다.',
                'has_reply': False,
                'reply': None
            },
            {
                'review_id': 'naver-review-003-004',
                'author': '건강한생활',
                'date': (datetime.now() - timedelta(days=6)).strftime('%Y.%m.%d'),
                'rating': 5,
                'content': '통밀빵이 정말 건강하고 맛있어요. 재료도 좋은 것만 쓰시는 것 같아요.',
                'has_reply': False,
                'reply': None
            }
        ]
        
        return reviews_by_place
    
    async def login(self, username: str, password: str) -> Dict:
        """Mock login to Naver"""
        logger.info(f"🎭 Mock Naver login: {username}")
        
        # Simulate login
        self.logged_in = True
        
        return {
            'success': True,
            'message': 'Successfully logged in to Naver (MOCK MODE)'
        }
    
    async def check_login_status(self) -> Dict:
        """Mock check login status"""
        logger.info("🎭 Mock checking Naver login status")
        
        return {
            'logged_in': self.logged_in,
            'message': 'Logged in to Naver (MOCK MODE)' if self.logged_in else 'Not logged in'
        }
    
    async def get_places(self) -> List[Dict]:
        """Get mock Naver places"""
        logger.info(f"🎭 Returning {len(self.mock_places)} mock Naver places")
        
        if not self.logged_in:
            logger.warning("🎭 Not logged in to Naver (Mock)")
            return []
        
        return self.mock_places
    
    async def get_reviews(self, place_id: str) -> List[Dict]:
        """Get mock reviews for a place"""
        logger.info(f"🎭 Returning mock Naver reviews for {place_id}")
        
        if not self.logged_in:
            logger.warning("🎭 Not logged in to Naver (Mock)")
            return []
        
        reviews = self.mock_reviews.get(place_id, [])
        logger.info(f"🎭 Found {len(reviews)} mock reviews for {place_id}")
        
        return reviews
    
    async def post_reply(self, place_id: str, review_id: str, reply_text: str) -> Dict:
        """Mock posting a reply to a review"""
        logger.info(f"🎭 Mock posting Naver reply to {review_id}")
        
        if not self.logged_in:
            return {
                'success': False,
                'message': 'Not logged in to Naver'
            }
        
        # In mock mode, just log and return success
        return {
            'success': True,
            'message': 'Reply posted successfully (MOCK MODE)',
            'review_id': review_id
        }
    
    async def logout(self) -> Dict:
        """Mock logout from Naver"""
        logger.info("🎭 Mock Naver logout")
        
        self.logged_in = False
        
        return {
            'success': True,
            'message': 'Successfully logged out (MOCK MODE)'
        }


# Create singleton instance
mock_naver_service = MockNaverService()





