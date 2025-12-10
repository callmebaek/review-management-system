from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from config import settings
from models.schemas import (
    GBPAccount, GBPLocation, ReviewsResponse, ReviewFilter,
    PostReplyRequest, PostReplyResponse
)

router = APIRouter()

# Choose service based on configuration
if settings.use_mock_gbp:
    from services.mock_gbp_service import mock_gbp_service as gbp_service
    print("🎭 Using MOCK GBP Service")
else:
    from services.gbp_service import gbp_service
    print("✅ Using REAL GBP Service")


@router.get("/accounts", response_model=List[GBPAccount])
async def get_accounts():
    """
    Get list of Google Business Profile accounts
    """
    return gbp_service.get_accounts()


@router.get("/locations", response_model=List[GBPLocation])
async def get_locations(account_name: Optional[str] = Query(None)):
    """
    Get list of business locations
    
    Args:
        account_name: Optional account name to filter locations
    """
    return gbp_service.get_locations(account_name)


@router.get("/reviews", response_model=ReviewsResponse)
async def get_reviews(
    location_name: str = Query(..., description="Full location resource name"),
    filter: ReviewFilter = Query(ReviewFilter.ALL, description="Filter by reply status"),
    page_size: int = Query(50, ge=1, le=100, description="Number of reviews to fetch")
):
    """
    Get reviews for a specific location
    
    Args:
        location_name: Full location resource name (e.g., "accounts/123/locations/456")
        filter: Filter by reply status (all, replied, unreplied)
        page_size: Number of reviews to fetch (1-100)
    """
    return gbp_service.get_reviews(location_name, filter, page_size)


@router.post("/reviews/reply", response_model=PostReplyResponse)
async def post_review_reply(request: PostReplyRequest):
    """
    Post a reply to a review
    
    Args:
        request: Reply request containing review_id, reply_text, and location_name
    """
    try:
        # Construct full review name
        review_name = f"{request.location_name}/reviews/{request.review_id}"
        
        result = gbp_service.post_reply(review_name, request.reply_text)
        
        return PostReplyResponse(
            success=result['success'],
            message=result['message'],
            review_id=request.review_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/reviews/{review_id}/reply")
async def delete_review_reply(
    review_id: str,
    location_name: str = Query(..., description="Full location resource name")
):
    """
    Delete a reply to a review
    
    Args:
        review_id: Review ID
        location_name: Full location resource name
    """
    try:
        review_name = f"{location_name}/reviews/{review_id}"
        result = gbp_service.delete_reply(review_name)
        
        return {
            'success': result['success'],
            'message': result['message'],
            'review_id': review_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



