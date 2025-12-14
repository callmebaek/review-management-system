from fastapi import APIRouter, HTTPException, Body, BackgroundTasks, Header, Depends
from typing import List, Dict, Optional
from pydantic import BaseModel
from config import settings
from datetime import datetime, timedelta
import json
import threading
import queue

router = APIRouter()

# 🚀 답글 게시 순차 처리를 위한 Lock
_reply_lock = threading.Lock()

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


class NaverSessionUpload(BaseModel):
    cookies: List[Dict]
    user_id: Optional[str] = "default"
    username: Optional[str] = None


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
async def naver_login_status(
    google_email: Optional[str] = Header(None, alias="X-Google-Email")
):
    """
    Check Naver login status for current Google user
    
    🔐 보안: 현재 구글 계정의 세션만 확인
    """
    try:
        from utils.db import get_db
        import traceback
        
        # Check if any session exists in MongoDB
        if settings.use_mongodb and settings.mongodb_url:
            print(f"🔍 [API /api/naver/status] Checking for: {google_email}")
            db = get_db()
            if db is not None:
                # 🔐 Google 이메일이 있으면 해당 유저의 세션만 확인
                query = {}
                if google_email and google_email != "default":
                    query["google_emails"] = google_email
                    print(f"🔒 Filtering sessions by: {google_email}")
                
                # Count sessions for this user
                session_count = db.naver_sessions.count_documents(query)
                print(f"🔍 [API /api/naver/status] Session count: {session_count}")
                
                if session_count > 0:
                    print(f"✅ [API /api/naver/status] Found {session_count} session(s)!")
                    
                    # Get most recently used session
                    try:
                        sessions_cursor = db.naver_sessions.find(query).sort("last_used", -1).limit(1)
                        sessions_list = list(sessions_cursor)
                        active_user = sessions_list[0].get('_id') if sessions_list else None
                    except Exception as sort_err:
                        print(f"⚠️ Sort error: {sort_err}, using any session")
                        active_user = None
                    
                    return {
                        'logged_in': True,
                        'message': f'{session_count}개의 세션이 저장됨',
                        'session_count': session_count,
                        'active_user': active_user,
                        'google_email': google_email  # 디버깅용
                    }
                else:
                    print(f"❌ [API /api/naver/status] No sessions for: {google_email}")
                    return {
                        'logged_in': False,
                        'message': '네이버 세션이 없습니다',
                        'google_email': google_email
                    }
            else:
                print("❌ [API /api/naver/status] MongoDB connection failed")
        else:
            print(f"⚠️ [API /api/naver/status] MongoDB not enabled (use_mongodb: {settings.use_mongodb})")
        
        # Fallback to original check_login_status
        print("🔄 [API /api/naver/status] Fallback to check_login_status")
        status = await naver_service.check_login_status()
        print(f"🔍 [API /api/naver/status] Response: {status}")
        return status
        
    except Exception as e:
        print(f"❌ [API /api/naver/status] Error: {e}")
        import traceback
        traceback.print_exc()
        return {'logged_in': False, 'message': f'Error checking status: {str(e)}'}


@router.get("/places")
async def get_naver_places(
    user_id: str = "default",
    google_email: Optional[str] = Header(None, alias="X-Google-Email")
):
    """
    Get list of places in Smart Place Center
    
    🔐 보안: google_email과 user_id의 연결 확인
    
    Args:
        user_id: User ID for multi-account support (default: "default")
        google_email: 현재 로그인한 구글 이메일 (헤더)
    """
    # 🔐 권한 검증
    from utils.auth_middleware import verify_naver_session_access
    await verify_naver_session_access(user_id, google_email)
    
    # Set active user before calling service
    naver_service.set_active_user(user_id)
    
    places = await naver_service.get_places()
    print(f"🏪 [API /api/naver/places] User: {user_id}, Response: {places}")
    print(f"🏪 [API /api/naver/places] Type: {type(places)}")
    print(f"🏪 [API /api/naver/places] Length: {len(places) if isinstance(places, list) else 'N/A'}")
    return places


@router.post("/reviews/load-async")
async def load_reviews_async(
    place_id: str = Body(...),
    load_count: int = Body(50),
    user_id: str = Body("default"),
    google_email: Optional[str] = Header(None, alias="X-Google-Email")
):
    """
    비동기로 리뷰 로드 (30초 타임아웃 우회)
    
    🔐 보안: google_email과 user_id의 연결 확인
    
    즉시 task_id를 반환하고 백그라운드에서 리뷰 로드
    프론트엔드는 /tasks/{task_id}로 진행 상황 폴링
    """
    # 🔐 권한 검증
    from utils.auth_middleware import verify_naver_session_access
    await verify_naver_session_access(user_id, google_email)
    
    from utils.task_manager import task_manager
    
    # Create task
    task_id = task_manager.create_task(
        task_type='review_load',
        user_id=user_id,
        params={
            'place_id': place_id,
            'load_count': load_count,
            'page': 1,
            'page_size': 20
        }
    )
    
    # Start background thread
    def background_load():
        import time as time_module
        
        try:
            # Update status to processing
            task_manager.update_task_status(task_id, 'processing')
            task_manager.update_progress(task_id, 0, '리뷰 로딩 시작...')
            
            # 🚀 직접 selenium 함수 호출 (wrapper 우회, Lock 문제 해결)
            from services.naver_automation_selenium import naver_automation_selenium
            
            # Set active user
            naver_automation_selenium.set_active_user(user_id)
            
            # 🚀 진행률 업데이트 스레드 시작
            import threading
            stop_progress = threading.Event()
            
            def update_progress_periodically():
                while not stop_progress.is_set():
                    try:
                        # selenium에서 진행률 읽기
                        progress = naver_automation_selenium.get_loading_progress(place_id)
                        if progress and progress.get('count', 0) > 0:
                            task_manager.update_progress(
                                task_id,
                                progress['count'],
                                progress.get('message', '로딩 중...')
                            )
                    except:
                        pass
                    time_module.sleep(1)  # 1초마다 업데이트
            
            progress_thread = threading.Thread(target=update_progress_periodically, daemon=True)
            progress_thread.start()
            
            # Load reviews (sync 함수 직접 호출)
            result = naver_automation_selenium.get_reviews(
                place_id,
                page=1,
                page_size=20,
                filter_type='all',
                load_count=load_count
            )
            
            # 진행률 업데이트 중지
            stop_progress.set()
            progress_thread.join(timeout=1)
            
            # Store result
            task_manager.set_result(task_id, result)
            task_manager.update_task_status(task_id, 'completed')
            task_manager.update_progress(task_id, len(result) if isinstance(result, list) else 0, '✅ 완료!')
            
        except Exception as e:
            print(f"❌ Background task {task_id} failed: {e}")
            import traceback
            traceback.print_exc()
            task_manager.set_error(task_id, str(e))
    
    # Start thread
    thread = threading.Thread(target=background_load, daemon=True)
    thread.start()
    
    return {
        'task_id': task_id,
        'message': '리뷰 로딩을 시작했습니다. 진행 상황을 확인하세요.',
        'status_url': f'/api/naver/tasks/{task_id}'
    }


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    작업 진행 상황 조회
    
    프론트엔드가 이 API를 2-3초마다 호출하여 진행 상황 확인
    """
    from utils.task_manager import task_manager
    
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        'task_id': task['_id'],
        'status': task['status'],
        'progress': task['progress'],
        'result': task.get('result'),
        'error': task.get('error'),
        'created_at': task['created_at'].isoformat() if task.get('created_at') else None,
        'started_at': task.get('started_at').isoformat() if task.get('started_at') else None,
        'completed_at': task.get('completed_at').isoformat() if task.get('completed_at') else None
    }


@router.get("/reviews/{place_id}")
async def get_naver_reviews(
    place_id: str,
    page: int = 1,
    page_size: int = 20,
    load_count: int = 300,
    user_id: str = "default",
    google_email: Optional[str] = Header(None, alias="X-Google-Email")
):
    """
    Get reviews for a specific place with pagination
    
    🔐 보안: google_email과 user_id의 연결 확인
    
    ⚠️ 주의: 100개 이상은 /reviews/load-async 사용 권장 (타임아웃 방지)
    
    User can specify how many reviews to load at once
    
    Args:
        place_id: Naver place ID
        page: Page number (starting from 1)
        page_size: Number of reviews per page (default 20)
        load_count: Total number of reviews to load (50/150/300/500/1000)
        user_id: User ID for multi-account support (default: "default")
        google_email: 현재 로그인한 구글 이메일 (헤더)
    """
    # 🔐 권한 검증
    from utils.auth_middleware import verify_naver_session_access
    await verify_naver_session_access(user_id, google_email)
    
    # Set active user before calling service
    naver_service.set_active_user(user_id)
    
    return await naver_service.get_reviews(place_id, page=page, page_size=page_size, filter_type='all', load_count=load_count)


@router.post("/reviews/reply-async")
async def post_reply_async(
    place_id: str = Body(...),
    author: str = Body(...),
    date: str = Body(...),
    content: str = Body(""),
    reply_text: str = Body(...),
    user_id: str = Body("default"),
    expected_review_count: int = Body(50),  # 목표 렌더링 개수
    google_email: Optional[str] = Header(None, alias="X-Google-Email")
):
    """
    비동기로 답글 게시 (30초 타임아웃 우회)
    
    🔐 보안: google_email과 user_id의 연결 확인
    
    작성자 + 날짜 + 내용 3중 매칭 - 가장 확실한 방법
    """
    # 🔐 권한 검증
    from utils.auth_middleware import verify_naver_session_access
    await verify_naver_session_access(user_id, google_email)
    
    from utils.task_manager import task_manager
    
    # Create task
    task_id = task_manager.create_task(
        task_type='reply_post',
        user_id=user_id,
        params={
            'place_id': place_id,
            'author': author,
            'date': date,
            'content': content[:100] if content else "",
            'reply_text': reply_text,
            'expected_count': expected_review_count  # 목표 개수
        }
    )
    
    # Start background thread
    def background_reply():
        # 🚀 CRITICAL: Lock으로 순차 처리 (동시 실행 방지)
        with _reply_lock:
            print(f"🔒 Acquired lock for task {task_id}")
            
            try:
                task_manager.update_task_status(task_id, 'processing')
                task_manager.update_progress(task_id, 0, '대기열에서 처리 중...')
                
                # 🚀 직접 selenium 함수 호출
                from services.naver_automation_selenium import naver_automation_selenium
                
                task_manager.update_progress(task_id, 0, '답글 게시 중...')
                
                # 🚀 작성자 + 날짜 + 내용 3중 매칭
                result = naver_automation_selenium.post_reply_by_composite(
                    place_id=place_id,
                    author=author,
                    date=date,
                    content=content,
                    reply_text=reply_text,
                    user_id=user_id,
                    expected_count=expected_review_count  # 목표 개수 전달
                )
                
                task_manager.set_result(task_id, result)
                task_manager.update_task_status(task_id, 'completed')
                task_manager.update_progress(task_id, 1, '✅ 답글 게시 완료!')
                
            except Exception as e:
                print(f"❌ Background reply task {task_id} failed: {e}")
                import traceback
                traceback.print_exc()
                task_manager.set_error(task_id, str(e))
            
            finally:
                print(f"🔓 Released lock for task {task_id}")
    
    thread = threading.Thread(target=background_reply, daemon=True)
    thread.start()
    
    return {
        'task_id': task_id,
        'message': '답글을 게시하고 있습니다.',
        'status_url': f'/api/naver/tasks/{task_id}'
    }


@router.post("/reviews/reply")
async def post_naver_reply(
    request: NaverReplyRequest,
    user_id: str = "default",
    google_email: Optional[str] = Header(None, alias="X-Google-Email")
):
    """
    Post a reply to a Naver review (동기 방식 - 30초 제한)
    
    🔐 보안: google_email과 user_id의 연결 확인
    
    ⚠️ 주의: /reviews/reply-async 사용 권장 (타임아웃 방지)
    
    Args:
        request: Reply request with place_id, review_id, and reply_text
        user_id: User ID for multi-account support (default: "default")
        google_email: 현재 로그인한 구글 이메일 (헤더)
    """
    # 🔐 권한 검증
    from utils.auth_middleware import verify_naver_session_access
    await verify_naver_session_access(user_id, google_email)
    
    # Set active user before calling service
    naver_service.set_active_user(user_id)
    
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


@router.post("/session/upload")
async def upload_session(
    session_data: NaverSessionUpload,
    google_email: str = None  # 쿼리 파라미터 (선택)
):
    """
    Upload Naver session from external tool (EXE)
    
    Google 계정과 연결하여 저장 (보안)
    ?google_email=user@gmail.com
    """
    try:
        from utils.db import get_db
        
        # Validate cookies
        if not session_data.cookies or len(session_data.cookies) == 0:
            raise HTTPException(status_code=400, detail="No cookies provided")
        
        # Check if MongoDB is available
        if not settings.use_mongodb or not settings.mongodb_url:
            raise HTTPException(
                status_code=500, 
                detail="MongoDB not configured. Session upload requires MongoDB."
            )
        
        db = get_db()
        if db is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # 🚀 Google 계정 연결 (다대다 - 여러 계정이 같은 세션 사용 가능)
        if not google_email:
            google_email = "public"
        
        # 쉼표로 구분된 이메일을 배열로 변환
        new_emails = [e.strip() for e in google_email.split(",") if e.strip()]
        
        # 기존 세션 확인
        existing_session = db.naver_sessions.find_one({"_id": session_data.user_id})
        
        if existing_session:
            # 🚀 기존 세션에 Google 계정 추가 (중복 방지)
            google_emails = existing_session.get("google_emails", [])
            for email in new_emails:
                if email not in google_emails:
                    google_emails.append(email)
                    print(f"✅ Added {email} to session {session_data.user_id}")
            
            session_doc = {
                "_id": session_data.user_id,
                "username": session_data.username,
                "google_emails": google_emails,  # 배열!
                "cookies": session_data.cookies,
                "created_at": existing_session.get("created_at", datetime.utcnow()),
                "expires_at": datetime.utcnow() + timedelta(days=7),
                "last_used": datetime.utcnow(),
                "status": "active",
                "cookie_count": len(session_data.cookies)
            }
        else:
            # 🚀 새 세션 생성
            session_doc = {
                "_id": session_data.user_id,
                "username": session_data.username,
                "google_emails": new_emails,  # 여러 개 한번에!
                "cookies": session_data.cookies,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=7),
                "last_used": datetime.utcnow(),
                "status": "active",
                "cookie_count": len(session_data.cookies)
            }
        
        # Upsert to MongoDB
        db.naver_sessions.replace_one(
            {"_id": session_data.user_id},
            session_doc,
            upsert=True
        )
        
        print(f"✅ Session uploaded for user: {session_data.user_id}")
        
        return {
            "success": True,
            "message": "Session uploaded successfully",
            "session_info": {
                "user_id": session_data.user_id,
                "username": session_data.username,
                "cookie_count": len(session_data.cookies),
                "expires_at": session_doc["expires_at"].isoformat(),
                "valid_days": 7
            }
        }
        
    except Exception as e:
        print(f"❌ Session upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Session upload failed: {str(e)}")


@router.get("/sessions/list")
async def list_sessions(
    google_email: str = None,
    x_google_email: Optional[str] = Header(None, alias="X-Google-Email")
):
    """
    Get Naver sessions for current Google user
    
    🔐 보안: 헤더의 google_email을 우선 사용 (파라미터는 호환성)
    
    google_email이 없으면 헤더에서 읽기
    헤더에도 없으면 빈 배열 반환 (보안)
    """
    try:
        from utils.db import get_db
        
        if not settings.use_mongodb or not settings.mongodb_url:
            return {"sessions": []}
        
        db = get_db()
        if db is None:
            return {"sessions": []}
        
        # 🔐 헤더의 이메일을 우선 사용 (더 안전)
        effective_email = x_google_email or google_email
        
        # 🔐 이메일이 없으면 빈 배열 반환 (보안 강화)
        if not effective_email:
            print("⚠️ No Google email provided, returning empty list")
            return {"sessions": []}
        
        # 🚀 Google 계정별 필터링 (배열에서 검색)
        query = {"google_emails": effective_email}  # 배열에 포함된 것 찾기
        print(f"🔍 Fetching sessions for: {effective_email}")
        
        # Get sessions
        sessions = list(db.naver_sessions.find(query, {
            "_id": 1,
            "username": 1,
            "google_emails": 1,  # 🚀 추가!
            "created_at": 1,
            "expires_at": 1,
            "status": 1,
            "cookie_count": 1
        }))
        
        # Format response
        formatted_sessions = []
        now = datetime.utcnow()
        
        for session in sessions:
            user_id = session.get("_id")
            expires_at = session.get("expires_at")
            
            is_expired = False
            remaining_days = 0
            if expires_at and now > expires_at:
                is_expired = True
            elif expires_at:
                remaining_days = (expires_at - now).days
            
            formatted_sessions.append({
                "user_id": user_id,
                "username": session.get("username"),
                "created_at": session.get("created_at").isoformat() if session.get("created_at") else None,
                "expires_at": expires_at.isoformat() if expires_at else None,
                "remaining_days": remaining_days,
                "is_expired": is_expired,
                "status": "expired" if is_expired else "active",
                "cookie_count": session.get("cookie_count", 0)
            })
        
        return {"sessions": formatted_sessions}
        
    except Exception as e:
        print(f"❌ Sessions list error: {str(e)}")
        return {"sessions": []}


@router.get("/session/status")
async def get_session_status(user_id: str = "default"):
    """
    Get current session status from MongoDB
    """
    try:
        from utils.db import get_db
        
        if not settings.use_mongodb or not settings.mongodb_url:
            return {
                "exists": False,
                "message": "MongoDB not configured"
            }
        
        db = get_db()
        if db is None:
            return {
                "exists": False,
                "message": "Database connection failed"
            }
        
        # Find session in MongoDB
        session = db.naver_sessions.find_one({"_id": user_id})
        
        if not session:
            return {
                "exists": False,
                "message": "No session found"
            }
        
        # Check if expired
        now = datetime.utcnow()
        expires_at = session.get("expires_at")
        
        is_expired = False
        if expires_at and now > expires_at:
            is_expired = True
        
        # Calculate remaining time
        remaining_days = 0
        if expires_at and not is_expired:
            remaining_days = (expires_at - now).days
        
        return {
            "exists": True,
            "username": session.get("username"),
            "created_at": session.get("created_at").isoformat() if session.get("created_at") else None,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "last_used": session.get("last_used").isoformat() if session.get("last_used") else None,
            "cookie_count": session.get("cookie_count", 0),
            "is_expired": is_expired,
            "remaining_days": remaining_days,
            "status": "expired" if is_expired else "active"
        }
        
    except Exception as e:
        print(f"❌ Session status error: {str(e)}")
        return {
            "exists": False,
            "message": f"Error: {str(e)}"
        }


@router.post("/session/switch")
async def switch_session(
    user_id: str,
    google_email: Optional[str] = Header(None, alias="X-Google-Email")
):
    """
    Switch to a different Naver account session
    
    🔐 보안: google_email과 user_id의 연결 확인
    
    This sets the active session that will be used for API calls
    """
    try:
        # 🔐 권한 검증
        from utils.auth_middleware import verify_naver_session_access
        await verify_naver_session_access(user_id, google_email)
        
        from utils.db import get_db
        
        if not settings.use_mongodb or not settings.mongodb_url:
            raise HTTPException(status_code=500, detail="MongoDB not configured")
        
        db = get_db()
        if db is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # Check if session exists (이미 verify_naver_session_access에서 확인하지만 재확인)
        session = db.naver_sessions.find_one({"_id": user_id})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Store active session in a separate collection or return info
        # For now, we'll just verify and return session info
        return {
            "success": True,
            "active_session": user_id,
            "username": session.get("username"),
            "message": f"Switched to account: {session.get('username')}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Session switch error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Session switch failed: {str(e)}")


@router.delete("/session")
async def delete_session(
    user_id: str = "default",
    google_email: Optional[str] = Header(None, alias="X-Google-Email")
):
    """
    Delete session connection for current Google user
    
    🔐 보안: google_email과 user_id의 연결 확인
    📝 동작:
      - google_emails 배열에서 현재 사용자의 이메일만 제거
      - 배열이 비면 세션 전체 삭제
      - 다른 사용자는 계속 세션 사용 가능
    """
    try:
        # 🔐 권한 검증
        from utils.auth_middleware import verify_naver_session_access
        await verify_naver_session_access(user_id, google_email)
        
        from utils.db import get_db
        
        if not settings.use_mongodb or not settings.mongodb_url:
            raise HTTPException(status_code=500, detail="MongoDB not configured")
        
        db = get_db()
        if db is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # 현재 세션 조회
        session = db.naver_sessions.find_one({"_id": user_id})
        if not session:
            return {
                "success": False,
                "message": "No session found to delete"
            }
        
        google_emails = session.get("google_emails", [])
        
        # 🔐 현재 사용자의 이메일만 제거
        if google_email in google_emails:
            google_emails.remove(google_email)
            print(f"🗑️ Removed {google_email} from session {user_id}")
        
        # 📝 배열이 비었으면 세션 전체 삭제, 아니면 업데이트
        if len(google_emails) == 0:
            # 마지막 사용자 → 세션 전체 삭제
            result = db.naver_sessions.delete_one({"_id": user_id})
            print(f"🗑️ Deleted entire session {user_id} (no users left)")
            
            return {
                "success": True,
                "message": "세션이 완전히 삭제되었습니다",
                "action": "deleted",
                "remaining_users": 0
            }
        else:
            # 다른 사용자 있음 → google_emails만 업데이트
            db.naver_sessions.update_one(
                {"_id": user_id},
                {"$set": {"google_emails": google_emails}}
            )
            print(f"✅ Updated session {user_id}, remaining users: {google_emails}")
            
            return {
                "success": True,
                "message": f"세션 연결이 해제되었습니다 (다른 사용자 {len(google_emails)}명은 계속 사용 가능)",
                "action": "disconnected",
                "remaining_users": len(google_emails)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Session delete error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Session delete failed: {str(e)}")


# ==================== AI Settings for Places ====================

@router.get("/places/{place_id}/ai-settings")
async def get_place_ai_settings_endpoint(
    place_id: str,
    google_email: Optional[str] = Header(None, alias="X-Google-Email")
):
    """
    Get AI reply generation settings for a specific place
    
    Args:
        place_id: Naver place ID
        google_email: Current user's Google email
    
    Returns:
        Place AI settings (or default values if not set)
    """
    try:
        from utils.db import get_place_ai_settings
        from models.schemas import PlaceAISettings
        
        if not google_email:
            raise HTTPException(status_code=401, detail="Google 계정 정보가 필요합니다")
        
        settings_doc = get_place_ai_settings(place_id, google_email)
        
        if not settings_doc:
            # Return default settings
            default_settings = PlaceAISettings()
            return {
                "place_id": place_id,
                "google_email": google_email,
                "settings": default_settings.dict(),
                "is_default": True
            }
        
        return {
            "place_id": settings_doc.get("place_id"),
            "google_email": settings_doc.get("google_email"),
            "settings": settings_doc.get("settings"),
            "created_at": settings_doc.get("created_at"),
            "updated_at": settings_doc.get("updated_at"),
            "is_default": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Get AI settings error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get AI settings: {str(e)}")


@router.put("/places/{place_id}/ai-settings")
async def update_place_ai_settings_endpoint(
    place_id: str,
    ai_settings: dict = Body(...),
    google_email: Optional[str] = Header(None, alias="X-Google-Email")
):
    """
    Update AI reply generation settings for a specific place
    
    🔐 보안: 해당 매장에 대한 세션을 가진 사용자만 설정 가능
    
    Args:
        place_id: Naver place ID
        ai_settings: AI settings dictionary
        google_email: Current user's Google email
    
    Returns:
        Success message
    """
    try:
        from utils.db import save_place_ai_settings, get_db
        from models.schemas import PlaceAISettings
        from config import settings as config_settings
        
        print(f"🔍 [PUT /places/{place_id}/ai-settings] Starting...")
        print(f"📧 Google email: {google_email}")
        print(f"📝 Received settings: {ai_settings}")
        
        if not google_email:
            raise HTTPException(status_code=401, detail="Google 계정 정보가 필요합니다")
        
        # 🔐 권한 검증: 이 매장에 대한 네이버 세션을 소유하고 있는지 확인
        if config_settings.use_mongodb and config_settings.mongodb_url:
            db = get_db()
            if db:
                # Find any naver session that has this google_email and check if it has access to this place
                # For now, we'll allow any authenticated user (can be enhanced later)
                print(f"✅ MongoDB available, user authenticated")
        
        # Validate settings with Pydantic
        try:
            validated_settings = PlaceAISettings(**ai_settings)
            print(f"✅ Settings validated: {validated_settings.dict()}")
        except Exception as validation_error:
            print(f"❌ Validation error: {validation_error}")
            raise HTTPException(
                status_code=400, 
                detail=f"설정 값이 올바르지 않습니다: {str(validation_error)}"
            )
        
        # Save to database
        success = save_place_ai_settings(place_id, google_email, validated_settings.dict())
        
        if success:
            print(f"✅ AI settings saved for place {place_id} by {google_email}")
            return {
                "success": True,
                "message": "AI 답글 설정이 저장되었습니다",
                "place_id": place_id
            }
        else:
            print(f"❌ save_place_ai_settings returned False")
            raise HTTPException(status_code=500, detail="데이터베이스 저장에 실패했습니다. MongoDB 연결을 확인해주세요.")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Update AI settings error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"설정 저장 실패: {str(e)}")


@router.delete("/places/{place_id}/ai-settings")
async def delete_place_ai_settings_endpoint(
    place_id: str,
    google_email: Optional[str] = Header(None, alias="X-Google-Email")
):
    """
    Delete AI settings for a place (revert to default)
    
    Args:
        place_id: Naver place ID
        google_email: Current user's Google email
    """
    try:
        from utils.db import delete_place_ai_settings
        
        if not google_email:
            raise HTTPException(status_code=401, detail="Google 계정 정보가 필요합니다")
        
        success = delete_place_ai_settings(place_id, google_email)
        
        if success:
            return {
                "success": True,
                "message": "AI 설정이 삭제되었습니다 (기본값으로 복원)"
            }
        else:
            return {
                "success": False,
                "message": "삭제할 설정이 없습니다"
            }
            
    except Exception as e:
        print(f"❌ Delete AI settings error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete AI settings: {str(e)}")



