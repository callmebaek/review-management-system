from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from typing import List, Optional, Dict
from utils.token_manager import token_manager
from models.schemas import (
    GBPAccount, GBPLocation, Review, ReviewsResponse, 
    ReviewerInfo, ReviewReply, ReviewFilter
)
from datetime import datetime
from fastapi import HTTPException
import logging
import traceback

logger = logging.getLogger(__name__)


class GBPService:
    """Service for interacting with Google Business Profile API"""
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.credentials = None
        self.service = None
    
    def _get_credentials(self) -> Credentials:
        """Get and validate credentials"""
        if not token_manager.token_exists(self.user_id):
            raise HTTPException(
                status_code=401,
                detail="Not authenticated. Please login first."
            )
        
        credentials = token_manager.load_token(self.user_id)
        
        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(GoogleRequest())
            token_manager.save_token(self.user_id, credentials)
        
        return credentials
    
    def _get_service(self):
        """Get authenticated Google My Business API service"""
        if not self.service:
            self.credentials = self._get_credentials()
            self.service = build('mybusinessbusinessinformation', 'v1', credentials=self.credentials)
        return self.service
    
    def get_accounts(self) -> List[GBPAccount]:
        """
        Get list of Google Business Profile accounts
        """
        try:
            logger.info("Attempting to get GBP accounts...")
            service = build('mybusinessaccountmanagement', 'v1', credentials=self._get_credentials())
            
            # List accounts
            logger.info("Calling accounts().list()...")
            response = service.accounts().list().execute()
            accounts = response.get('accounts', [])
            logger.info(f"Found {len(accounts)} accounts")
            
            return [
                GBPAccount(
                    name=account.get('name', ''),
                    account_name=account.get('accountName', ''),
                    type=account.get('type', ''),
                    role=account.get('role')
                )
                for account in accounts
            ]
            
        except Exception as e:
            logger.error(f"Error fetching accounts: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error fetching accounts: {str(e)}")
    
    def get_locations(self, account_name: Optional[str] = None) -> List[GBPLocation]:
        """
        Get list of business locations
        
        Args:
            account_name: Optional account name to filter locations
        """
        try:
            logger.info("Attempting to get GBP locations...")
            service = self._get_service()
            
            # If no account specified, get first account
            if not account_name:
                logger.info("No account specified, getting accounts first...")
                accounts = self.get_accounts()
                if not accounts:
                    logger.warning("No accounts found, returning empty locations list")
                    return []
                account_name = accounts[0].name
                logger.info(f"Using account: {account_name}")
            
            # List locations
            parent = account_name
            logger.info(f"Calling locations().list() with parent={parent}")
            response = service.locations().list(parent=parent, readMask='name,title,storefrontAddress,phoneNumbers').execute()
            locations = response.get('locations', [])
            logger.info(f"Found {len(locations)} locations")
            
            return [
                GBPLocation(
                    name=loc.get('name', ''),
                    location_name=loc.get('title', ''),
                    store_code=loc.get('storeCode'),
                    address=self._format_address(loc.get('storefrontAddress', {})),
                    phone=self._get_primary_phone(loc.get('phoneNumbers', []))
                )
                for loc in locations
            ]
            
        except Exception as e:
            logger.error(f"Error fetching locations: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error fetching locations: {str(e)}")
    
    def get_reviews(
        self, 
        location_name: str, 
        filter_type: ReviewFilter = ReviewFilter.ALL,
        page_size: int = 50
    ) -> ReviewsResponse:
        """
        Get reviews for a specific location
        
        Args:
            location_name: Full location resource name (e.g., "locations/12345")
            filter_type: Filter by reply status (all, replied, unreplied)
            page_size: Number of reviews to fetch
        """
        try:
            # Build API service for reviews
            service = build('mybusiness', 'v4', credentials=self._get_credentials())
            
            # Fetch reviews
            parent = f"{location_name}/reviews"
            response = service.accounts().locations().reviews().list(
                parent=location_name,
                pageSize=page_size
            ).execute()
            
            reviews_data = response.get('reviews', [])
            
            # Parse reviews
            reviews = []
            for review_data in reviews_data:
                # Filter by reply status
                has_reply = 'reviewReply' in review_data
                
                if filter_type == ReviewFilter.REPLIED and not has_reply:
                    continue
                elif filter_type == ReviewFilter.UNREPLIED and has_reply:
                    continue
                
                # Parse review
                review = self._parse_review(review_data)
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
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching reviews: {str(e)}")
    
    def post_reply(self, review_name: str, reply_text: str) -> Dict:
        """
        Post a reply to a review
        
        Args:
            review_name: Full review resource name
            reply_text: Reply text to post
        """
        try:
            service = build('mybusiness', 'v4', credentials=self._get_credentials())
            
            # Create reply
            reply_body = {
                'comment': reply_text
            }
            
            response = service.accounts().locations().reviews().updateReply(
                name=review_name,
                body={'reply': reply_body}
            ).execute()
            
            return {
                'success': True,
                'message': 'Reply posted successfully',
                'review_name': review_name
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error posting reply: {str(e)}")
    
    def delete_reply(self, review_name: str) -> Dict:
        """
        Delete a reply to a review
        
        Args:
            review_name: Full review resource name
        """
        try:
            service = build('mybusiness', 'v4', credentials=self._get_credentials())
            
            service.accounts().locations().reviews().deleteReply(
                name=review_name
            ).execute()
            
            return {
                'success': True,
                'message': 'Reply deleted successfully',
                'review_name': review_name
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting reply: {str(e)}")
    
    # Helper methods
    
    def _parse_review(self, review_data: Dict) -> Review:
        """Parse review data from API response"""
        reviewer_data = review_data.get('reviewer', {})
        reviewer = ReviewerInfo(
            display_name=reviewer_data.get('displayName', 'Anonymous'),
            profile_photo_url=reviewer_data.get('profilePhotoUrl'),
            is_anonymous=reviewer_data.get('isAnonymous', False)
        )
        
        review_reply = None
        if 'reviewReply' in review_data:
            reply_data = review_data['reviewReply']
            review_reply = ReviewReply(
                comment=reply_data.get('comment', ''),
                update_time=self._parse_timestamp(reply_data.get('updateTime'))
            )
        
        return Review(
            review_id=review_data.get('reviewId', ''),
            reviewer=reviewer,
            star_rating=review_data.get('starRating', 'STAR_RATING_UNSPECIFIED'),
            comment=review_data.get('comment'),
            create_time=self._parse_timestamp(review_data.get('createTime')),
            update_time=self._parse_timestamp(review_data.get('updateTime')),
            review_reply=review_reply,
            name=review_data.get('name', '')
        )
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> datetime:
        """Parse ISO timestamp string to datetime"""
        if not timestamp_str:
            return datetime.now()
        
        try:
            # Remove 'Z' and parse
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
    
    def _format_address(self, address: Dict) -> Optional[str]:
        """Format address dict to string"""
        if not address:
            return None
        
        parts = []
        if address.get('addressLines'):
            parts.extend(address['addressLines'])
        if address.get('locality'):
            parts.append(address['locality'])
        if address.get('administrativeArea'):
            parts.append(address['administrativeArea'])
        if address.get('postalCode'):
            parts.append(address['postalCode'])
        
        return ', '.join(parts) if parts else None
    
    def _get_primary_phone(self, phone_numbers: List[Dict]) -> Optional[str]:
        """Get primary phone number"""
        if not phone_numbers:
            return None
        
        # Find primary phone
        for phone in phone_numbers:
            if phone.get('type') == 'PRIMARY':
                return phone.get('phoneNumber')
        
        # Return first phone if no primary
        return phone_numbers[0].get('phoneNumber') if phone_numbers else None


# Create singleton instance
gbp_service = GBPService()



