"""
Custom Exceptions for Review Management System
"""

from fastapi import HTTPException


class BrowserSessionExpiredException(HTTPException):
    """브라우저 세션이 만료되어 재로그인이 필요한 경우"""
    
    def __init__(self, user_id: str = None):
        detail = "브라우저 세션이 만료되었습니다. 다시 로그인해주세요."
        if user_id:
            detail += f" (User: {user_id})"
        
        super().__init__(
            status_code=401,
            detail=detail,
            headers={"X-Require-Relogin": "true"}
        )

