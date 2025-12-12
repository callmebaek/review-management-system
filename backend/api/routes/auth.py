from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
import os
import requests  # 🔐 Google API 직접 호출용
from config import settings
from utils.token_manager import token_manager

router = APIRouter()

# OAuth 2.0 scopes
SCOPES = [
    'https://www.googleapis.com/auth/business.manage',
    'https://www.googleapis.com/auth/userinfo.email',  # 🔐 이메일 정보 가져오기
    'https://www.googleapis.com/auth/userinfo.profile',  # 🔐 프로필 정보 가져오기
    'openid',  # 🔐 OpenID Connect
]

# OAuth 2.0 client configuration
CLIENT_CONFIG = {
    "web": {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [settings.google_redirect_uri],
    }
}


def create_flow():
    """Create OAuth 2.0 flow"""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth credentials not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env file"
        )
    
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=settings.google_redirect_uri
    )
    return flow


@router.get("/google/login")
async def google_login():
    """
    Initiate Google OAuth 2.0 flow
    Returns authorization URL for user to authenticate
    """
    try:
        flow = create_flow()
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent screen to get refresh token
        )
        
        return {
            "authorization_url": authorization_url,
            "state": state,
            "debug_info": {
                "redirect_uri": settings.google_redirect_uri,
                "client_id": settings.google_client_id[:50] if settings.google_client_id else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/google/callback")
async def google_callback(request: Request):
    """
    Handle OAuth 2.0 callback
    Exchange authorization code for access token
    """
    try:
        # Get authorization code from query params
        code = request.query_params.get('code')
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code not found")
        
        # Exchange code for token
        flow = create_flow()
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        
        # 🚀 Get Google user info (email) - Using userinfo endpoint directly
        try:
            # 방법 1: Google UserInfo API를 직접 호출 (더 안정적)
            headers = {
                'Authorization': f'Bearer {credentials.token}'
            }
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                raise Exception(f"Google API returned {response.status_code}: {response.text}")
            
            user_info = response.json()
            user_email = user_info.get('email', None)
            user_name = user_info.get('name', '')
            
            # 🔐 이메일을 가져오지 못하면 에러 처리
            if not user_email:
                raise Exception("Failed to get email from Google")
            
            print(f"✅ Google user logged in: {user_email} ({user_name})")
            
        except Exception as e:
            print(f"❌ Failed to get Google user info: {e}")
            import traceback
            traceback.print_exc()
            
            # 프론트엔드에 에러 전달
            frontend_url = os.getenv("FRONTEND_URL", f"http://localhost:{settings.frontend_port}")
            return RedirectResponse(url=f"{frontend_url}/login?error=google_auth_failed")
        
        # Save credentials with email as user ID
        user_id = user_email
        token_manager.save_token(user_id, credentials)
        
        # 🚀 사용자 정보를 쿼리 파라미터로 전달
        import urllib.parse
        frontend_url = os.getenv("FRONTEND_URL", f"http://localhost:{settings.frontend_port}")
        redirect_url = f"{frontend_url}/dashboard?auth=success&email={urllib.parse.quote(user_email)}&name={urllib.parse.quote(user_name)}"
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        # Redirect to frontend with error
        frontend_url = os.getenv("FRONTEND_URL", f"http://localhost:{settings.frontend_port}")
        return RedirectResponse(url=f"{frontend_url}/login?error={str(e)}")


@router.get("/me")
async def get_current_user():
    """
    현재 로그인한 Google 사용자 정보 가져오기
    """
    # TODO: 실제 구현 (현재는 Mock)
    # 실제로는 세션이나 JWT에서 사용자 정보 가져오기
    return {
        "email": "user@example.com",  # Mock
        "authenticated": True
    }


@router.get("/status")
async def auth_status():
    """
    Check if user is authenticated
    """
    user_id = "default"
    
    if not token_manager.token_exists(user_id):
        return {
            "authenticated": False,
            "message": "No credentials found"
        }
    
    try:
        credentials = token_manager.load_token(user_id)
        
        # Check if token is valid
        if credentials and credentials.valid:
            return {
                "authenticated": True,
                "message": "Credentials are valid"
            }
        
        # Try to refresh token if expired
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(GoogleRequest())
            token_manager.save_token(user_id, credentials)
            return {
                "authenticated": True,
                "message": "Credentials refreshed"
            }
        
        return {
            "authenticated": False,
            "message": "Credentials expired and cannot be refreshed"
        }
        
    except Exception as e:
        return {
            "authenticated": False,
            "message": f"Error checking auth status: {str(e)}"
        }


@router.post("/logout")
async def logout():
    """
    Logout user by deleting stored credentials
    """
    user_id = "default"
    success = token_manager.delete_token(user_id)
    
    if success:
        return {"message": "Successfully logged out"}
    else:
        return {"message": "No credentials to delete"}


@router.get("/credentials")
async def get_credentials():
    """
    Get current credentials (for debugging - remove in production)
    """
    user_id = "default"
    
    if not token_manager.token_exists(user_id):
        raise HTTPException(status_code=404, detail="No credentials found")
    
    credentials = token_manager.load_token(user_id)
    
    # Check and refresh if needed
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(GoogleRequest())
        token_manager.save_token(user_id, credentials)
    
    return credentials



