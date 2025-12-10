"""
Mock Google Business Profile Service for testing without API access
"""
from typing import List, Optional, Dict
from models.schemas import (
    GBPAccount, GBPLocation, Review, ReviewsResponse, 
    ReviewerInfo, ReviewReply, ReviewFilter
)
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)


class MockGBPService:
    """Mock implementation of GBP service for testing"""
    
    def __init__(self):
        self.mock_accounts = self._create_mock_accounts()
        self.mock_locations = self._create_mock_locations()
        self.mock_reviews = self._create_mock_reviews()
        logger.info("🎭 Mock GBP Service initialized")
    
    def _create_mock_accounts(self) -> List[Dict]:
        """Create mock GBP accounts"""
        return [
            {
                'name': 'accounts/mock-account-123',
                'accountName': '테스트 비즈니스 계정',
                'type': 'PERSONAL',
                'role': 'OWNER'
            }
        ]
    
    def _create_mock_locations(self) -> List[Dict]:
        """Create mock business locations"""
        return [
            {
                'name': 'locations/mock-location-001',
                'title': '강남 카페 테스트',
                'storeCode': 'GN-001',
                'storefrontAddress': {
                    'addressLines': ['테헤란로 123'],
                    'locality': '강남구',
                    'administrativeArea': '서울특별시',
                    'postalCode': '06234'
                },
                'phoneNumbers': [
                    {'phoneNumber': '02-1234-5678', 'type': 'PRIMARY'}
                ]
            },
            {
                'name': 'locations/mock-location-002',
                'title': '홍대 레스토랑 테스트',
                'storeCode': 'HD-002',
                'storefrontAddress': {
                    'addressLines': ['양화로 456'],
                    'locality': '마포구',
                    'administrativeArea': '서울특별시',
                    'postalCode': '04044'
                },
                'phoneNumbers': [
                    {'phoneNumber': '02-9876-5432', 'type': 'PRIMARY'}
                ]
            },
            {
                'name': 'locations/mock-location-003',
                'title': '판교 베이커리 테스트',
                'storeCode': 'PG-003',
                'storefrontAddress': {
                    'addressLines': ['판교역로 789'],
                    'locality': '분당구',
                    'administrativeArea': '경기도',
                    'postalCode': '13494'
                },
                'phoneNumbers': [
                    {'phoneNumber': '031-1111-2222', 'type': 'PRIMARY'}
                ]
            }
        ]
    
    def _create_mock_reviews(self) -> Dict[str, List[Dict]]:
        """Create mock reviews for each location"""
        reviews_by_location = {}
        
        # Reviews for location 001 (강남 카페)
        reviews_by_location['locations/mock-location-001'] = [
            {
                'reviewId': 'review-001-001',
                'name': 'locations/mock-location-001/reviews/review-001-001',
                'reviewer': {
                    'displayName': '김민수',
                    'profilePhotoUrl': None,
                    'isAnonymous': False
                },
                'starRating': 'FIVE',
                'comment': '커피가 정말 맛있어요! 분위기도 좋고 직원분들도 친절하세요. 자주 방문하고 있습니다.',
                'createTime': (datetime.now() - timedelta(days=2)).isoformat() + 'Z',
                'updateTime': (datetime.now() - timedelta(days=2)).isoformat() + 'Z',
            },
            {
                'reviewId': 'review-001-002',
                'name': 'locations/mock-location-001/reviews/review-001-002',
                'reviewer': {
                    'displayName': '이영희',
                    'profilePhotoUrl': None,
                    'isAnonymous': False
                },
                'starRating': 'FOUR',
                'comment': '음료는 맛있는데 좌석이 조금 부족한 것 같아요. 그래도 재방문 의사 있습니다!',
                'createTime': (datetime.now() - timedelta(days=5)).isoformat() + 'Z',
                'updateTime': (datetime.now() - timedelta(days=5)).isoformat() + 'Z',
                'reviewReply': {
                    'comment': '소중한 리뷰 감사합니다! 좌석 관련하여 개선하도록 노력하겠습니다.',
                    'updateTime': (datetime.now() - timedelta(days=4)).isoformat() + 'Z'
                }
            },
            {
                'reviewId': 'review-001-003',
                'name': 'locations/mock-location-001/reviews/review-001-003',
                'reviewer': {
                    'displayName': '박철수',
                    'profilePhotoUrl': None,
                    'isAnonymous': False
                },
                'starRating': 'THREE',
                'comment': '보통이에요. 가격 대비 좀 비싼 것 같습니다.',
                'createTime': (datetime.now() - timedelta(days=7)).isoformat() + 'Z',
                'updateTime': (datetime.now() - timedelta(days=7)).isoformat() + 'Z',
            }
        ]
        
        # Reviews for location 002 (홍대 레스토랑)
        reviews_by_location['locations/mock-location-002'] = [
            {
                'reviewId': 'review-002-001',
                'name': 'locations/mock-location-002/reviews/review-002-001',
                'reviewer': {
                    'displayName': '정수아',
                    'profilePhotoUrl': None,
                    'isAnonymous': False
                },
                'starRating': 'FIVE',
                'comment': '음식이 정말 맛있고 분위기도 좋아요! 데이트 장소로 강력 추천합니다.',
                'createTime': (datetime.now() - timedelta(days=1)).isoformat() + 'Z',
                'updateTime': (datetime.now() - timedelta(days=1)).isoformat() + 'Z',
            },
            {
                'reviewId': 'review-002-002',
                'name': 'locations/mock-location-002/reviews/review-002-002',
                'reviewer': {
                    'displayName': '최동훈',
                    'profilePhotoUrl': None,
                    'isAnonymous': False
                },
                'starRating': 'TWO',
                'comment': '음식은 괜찮았는데 서비스가 너무 느렸어요. 대기 시간이 너무 길었습니다.',
                'createTime': (datetime.now() - timedelta(days=3)).isoformat() + 'Z',
                'updateTime': (datetime.now() - timedelta(days=3)).isoformat() + 'Z',
            }
        ]
        
        # Reviews for location 003 (판교 베이커리)
        reviews_by_location['locations/mock-location-003'] = [
            {
                'reviewId': 'review-003-001',
                'name': 'locations/mock-location-003/reviews/review-003-001',
                'reviewer': {
                    'displayName': '강지은',
                    'profilePhotoUrl': None,
                    'isAnonymous': False
                },
                'starRating': 'FIVE',
                'comment': '빵이 정말 신선하고 맛있어요! 특히 크루아상이 최고입니다. 매일 사먹고 싶어요.',
                'createTime': (datetime.now() - timedelta(hours=12)).isoformat() + 'Z',
                'updateTime': (datetime.now() - timedelta(hours=12)).isoformat() + 'Z',
            },
            {
                'reviewId': 'review-003-002',
                'name': 'locations/mock-location-003/reviews/review-003-002',
                'reviewer': {
                    'displayName': '윤태영',
                    'profilePhotoUrl': None,
                    'isAnonymous': False
                },
                'starRating': 'FOUR',
                'comment': '빵 맛은 좋은데 가격이 조금 비싸요. 그래도 품질을 생각하면 합리적인 것 같습니다.',
                'createTime': (datetime.now() - timedelta(days=4)).isoformat() + 'Z',
                'updateTime': (datetime.now() - timedelta(days=4)).isoformat() + 'Z',
                'reviewReply': {
                    'comment': '저희 제품을 좋아해주셔서 감사합니다! 항상 최고의 품질을 유지하도록 노력하겠습니다.',
                    'updateTime': (datetime.now() - timedelta(days=3)).isoformat() + 'Z'
                }
            },
            {
                'reviewId': 'review-003-003',
                'name': 'locations/mock-location-003/reviews/review-003-003',
                'reviewer': {
                    'displayName': '한지민',
                    'profilePhotoUrl': None,
                    'isAnonymous': False
                },
                'starRating': 'FIVE',
                'comment': '항상 친절하시고 빵도 맛있어요. 판교에서 최고의 베이커리입니다!',
                'createTime': (datetime.now() - timedelta(days=6)).isoformat() + 'Z',
                'updateTime': (datetime.now() - timedelta(days=6)).isoformat() + 'Z',
            }
        ]
        
        return reviews_by_location
    
    def get_accounts(self) -> List[GBPAccount]:
        """Get mock GBP accounts"""
        logger.info("🎭 Returning mock accounts")
        return [
            GBPAccount(
                name=account['name'],
                account_name=account['accountName'],
                type=account['type'],
                role=account.get('role')
            )
            for account in self.mock_accounts
        ]
    
    def get_locations(self, account_name: Optional[str] = None) -> List[GBPLocation]:
        """Get mock business locations"""
        logger.info(f"🎭 Returning {len(self.mock_locations)} mock locations")
        
        locations = []
        for loc in self.mock_locations:
            address_data = loc.get('storefrontAddress', {})
            address_parts = []
            if address_data.get('addressLines'):
                address_parts.extend(address_data['addressLines'])
            if address_data.get('locality'):
                address_parts.append(address_data['locality'])
            if address_data.get('administrativeArea'):
                address_parts.append(address_data['administrativeArea'])
            
            phone = None
            if loc.get('phoneNumbers'):
                phone = loc['phoneNumbers'][0].get('phoneNumber')
            
            locations.append(GBPLocation(
                name=loc['name'],
                location_name=loc['title'],
                store_code=loc.get('storeCode'),
                address=', '.join(address_parts) if address_parts else None,
                phone=phone
            ))
        
        return locations
    
    def get_reviews(
        self, 
        location_name: str, 
        filter_type: ReviewFilter = ReviewFilter.ALL,
        page_size: int = 50
    ) -> ReviewsResponse:
        """Get mock reviews for a location"""
        logger.info(f"🎭 Returning mock reviews for {location_name} (filter: {filter_type})")
        
        # Get reviews for this location
        reviews_data = self.mock_reviews.get(location_name, [])
        
        # Parse reviews
        reviews = []
        for review_data in reviews_data:
            has_reply = 'reviewReply' in review_data
            
            # Filter by reply status
            if filter_type == ReviewFilter.REPLIED and not has_reply:
                continue
            elif filter_type == ReviewFilter.UNREPLIED and has_reply:
                continue
            
            # Parse reviewer
            reviewer_data = review_data.get('reviewer', {})
            reviewer = ReviewerInfo(
                display_name=reviewer_data.get('displayName', 'Anonymous'),
                profile_photo_url=reviewer_data.get('profilePhotoUrl'),
                is_anonymous=reviewer_data.get('isAnonymous', False)
            )
            
            # Parse review reply
            review_reply = None
            if 'reviewReply' in review_data:
                reply_data = review_data['reviewReply']
                review_reply = ReviewReply(
                    comment=reply_data.get('comment', ''),
                    update_time=self._parse_timestamp(reply_data.get('updateTime'))
                )
            
            # Create review object
            review = Review(
                review_id=review_data.get('reviewId', ''),
                reviewer=reviewer,
                star_rating=review_data.get('starRating', 'STAR_RATING_UNSPECIFIED'),
                comment=review_data.get('comment'),
                create_time=self._parse_timestamp(review_data.get('createTime')),
                update_time=self._parse_timestamp(review_data.get('updateTime')),
                review_reply=review_reply,
                name=review_data.get('name', '')
            )
            reviews.append(review)
        
        # Calculate average rating
        avg_rating = None
        if reviews:
            ratings = [self._star_rating_to_int(r.star_rating) for r in reviews]
            avg_rating = sum(ratings) / len(ratings)
        
        return ReviewsResponse(
            reviews=reviews,
            total_count=len(reviews),
            average_rating=avg_rating
        )
    
    def post_reply(self, review_name: str, reply_text: str) -> Dict:
        """Mock posting a reply to a review"""
        logger.info(f"🎭 Mock posting reply to {review_name}")
        
        # In mock mode, just log and return success
        # In reality, we would update self.mock_reviews
        return {
            'success': True,
            'message': 'Reply posted successfully (MOCK MODE)',
            'review_name': review_name
        }
    
    def delete_reply(self, review_name: str) -> Dict:
        """Mock deleting a reply"""
        logger.info(f"🎭 Mock deleting reply from {review_name}")
        
        return {
            'success': True,
            'message': 'Reply deleted successfully (MOCK MODE)',
            'review_name': review_name
        }
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> datetime:
        """Parse ISO timestamp string to datetime"""
        if not timestamp_str:
            return datetime.now()
        
        try:
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1]
            return datetime.fromisoformat(timestamp_str)
        except:
            return datetime.now()
    
    def _star_rating_to_int(self, star_rating: str) -> int:
        """Convert star rating enum to integer"""
        mapping = {
            'ONE': 1,
            'TWO': 2,
            'THREE': 3,
            'FOUR': 4,
            'FIVE': 5,
        }
        return mapping.get(star_rating, 0)


# Create singleton instance
mock_gbp_service = MockGBPService()





