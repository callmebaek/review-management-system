"""
인증 미들웨어 - 네이버 세션 접근 권한 검증
Google 계정과 네이버 세션의 연결을 확인
"""
from fastapi import HTTPException, Header
from typing import Optional
from config import settings


async def verify_naver_session_access(
    user_id: str,
    google_email: Optional[str] = Header(None, alias="X-Google-Email")
) -> bool:
    """
    네이버 세션 접근 권한 검증
    
    Args:
        user_id: 네이버 세션 ID (네이버 아이디)
        google_email: 현재 로그인한 구글 이메일 (헤더에서 받음)
    
    Returns:
        bool: 접근 권한 있으면 True
        
    Raises:
        HTTPException: 권한이 없으면 403 에러
    """
    # MongoDB가 설정되지 않은 경우 검증 생략 (개발 모드)
    if not settings.use_mongodb or not settings.mongodb_url:
        print("⚠️ MongoDB not configured, skipping auth check")
        return True
    
    # Google 이메일이 없으면 거부
    if not google_email:
        raise HTTPException(
            status_code=401,
            detail="Google 계정 정보가 필요합니다. 다시 로그인해주세요."
        )
    
    try:
        from utils.db import get_db
        
        db = get_db()
        if db is None:
            # DB 연결 실패 시 경고하고 계속 진행 (서비스 중단 방지)
            print("⚠️ Database connection failed, skipping auth check")
            return True
        
        # 세션 조회
        session = db.naver_sessions.find_one({"_id": user_id})
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"네이버 세션을 찾을 수 없습니다. (세션 ID: {user_id})"
            )
        
        # google_emails 배열에서 확인
        google_emails = session.get("google_emails", [])
        
        # 🔐 권한 검증: 현재 로그인한 구글 계정이 세션에 등록되어 있는지 확인
        if google_email not in google_emails:
            print(f"🚫 Access denied: {google_email} tried to access {user_id}")
            print(f"   Authorized emails: {google_emails}")
            raise HTTPException(
                status_code=403,
                detail=f"이 네이버 세션에 접근할 권한이 없습니다. 계정: {user_id}"
            )
        
        # 🎉 권한 확인 완료
        print(f"✅ Access granted: {google_email} → {user_id}")
        return True
        
    except HTTPException:
        # HTTPException은 그대로 전달
        raise
    except Exception as e:
        print(f"❌ Auth check error: {e}")
        # 예기치 않은 오류 시 보수적으로 거부
        raise HTTPException(
            status_code=500,
            detail="세션 권한 확인 중 오류가 발생했습니다."
        )


async def get_google_email_from_header(
    google_email: Optional[str] = Header(None, alias="X-Google-Email")
) -> Optional[str]:
    """
    헤더에서 Google 이메일 추출 (선택적)
    
    Args:
        google_email: Google 이메일 (헤더)
    
    Returns:
        str: Google 이메일 또는 None
    """
    return google_email


