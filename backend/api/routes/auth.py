from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
import os
from config import settings
from utils.token_manager import token_manager

router = APIRouter()

# OAuth 2.0 scopes
SCOPES = [
    'https://www.googleapis.com/auth/business.manage',
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
        
        # Save credentials with user ID (for now, use 'default')
        # In production, you'd want to associate this with actual user accounts
        user_id = "default"
        token_manager.save_token(user_id, credentials)
        
        # Redirect to frontend success page
        # Use FRONTEND_URL from environment, fallback to localhost for local dev
        frontend_url = os.getenv("FRONTEND_URL", f"http://localhost:{settings.frontend_port}")
        return RedirectResponse(url=f"{frontend_url}/dashboard?auth=success")
        
    except Exception as e:
        # Redirect to frontend with error
        frontend_url = os.getenv("FRONTEND_URL", f"http://localhost:{settings.frontend_port}")
        return RedirectResponse(url=f"{frontend_url}/login?error={str(e)}")


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



