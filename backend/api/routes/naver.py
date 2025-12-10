from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict
from pydantic import BaseModel
from config import settings

router = APIRouter()

# Choose service based on configuration
if settings.use_mock_naver:
    from services.mock_naver_service import mock_naver_service as naver_service
    print("🎭 Using MOCK Naver Service")
else:
    from services.naver_automation_selenium_wrapper import naver_automation as naver_service
    print("✅ Using REAL Naver Service (Selenium - Python 3.13 Compatible!)")


class NaverLoginRequest(BaseModel):
    username: str
    password: str
    headless: bool = True


class NaverReplyRequest(BaseModel):
    place_id: str
    review_id: str
    reply_text: str


@router.post("/login")
async def naver_login(request: NaverLoginRequest):
    """
    Login to Naver Smart Place Center
    
    ⚠️ Warning: This is for personal use only.
    Naver does not provide official API for review management.
    """
    return await naver_service.login(
        username=request.username,
        password=request.password
    )


@router.get("/status")
async def naver_login_status():
    """
    Check Naver login status
    """
    status = await naver_service.check_login_status()
    print(f"🔍 [API /api/naver/status] Response: {status}")
    return status


@router.get("/places")
async def get_naver_places():
    """
    Get list of places in Smart Place Center
    """
    places = await naver_service.get_places()
    print(f"🏪 [API /api/naver/places] Response: {places}")
    print(f"🏪 [API /api/naver/places] Type: {type(places)}")
    print(f"🏪 [API /api/naver/places] Length: {len(places) if isinstance(places, list) else 'N/A'}")
    return places


@router.get("/reviews/{place_id}")
async def get_naver_reviews(place_id: str, page: int = 1, page_size: int = 20, load_count: int = 300):
    """
    Get reviews for a specific place with pagination
    
    User can specify how many reviews to load at once
    
    Args:
        place_id: Naver place ID
        page: Page number (starting from 1)
        page_size: Number of reviews per page (default 20)
        load_count: Total number of reviews to load (50/150/300/500/1000)
    """
    return await naver_service.get_reviews(place_id, page=page, page_size=page_size, filter_type='all', load_count=load_count)


@router.post("/reviews/reply")
async def post_naver_reply(request: NaverReplyRequest):
    """
    Post a reply to a Naver review
    
    Args:
        request: Reply request with place_id, review_id, and reply_text
    """
    return await naver_service.post_reply(
        place_id=request.place_id,
        review_id=request.review_id,
        reply_text=request.reply_text
    )


@router.get("/reviews/progress/{place_id}")
async def get_reviews_progress(place_id: str):
    """
    Get real-time loading progress for reviews
    
    Args:
        place_id: Naver place ID
    
    Returns:
        Progress status with count and message
    """
    progress = await naver_service.get_loading_progress(place_id)
    # Debug log to see what we're returning
    if progress.get('count', 0) > 0:
        print(f"📤 Sending progress: {progress}")
    return progress


@router.post("/logout")
async def naver_logout():
    """
    Logout from Naver and clear session
    """
    return await naver_service.logout()



