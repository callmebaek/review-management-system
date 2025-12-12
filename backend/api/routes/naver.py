from fastapi import APIRouter, HTTPException, Body, BackgroundTasks
from typing import List, Dict, Optional
from pydantic import BaseModel
from config import settings
from datetime import datetime, timedelta
import json
import threading

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
async def naver_login_status():
    """
    Check Naver login status (checks if ANY session exists in MongoDB)
    """
    try:
        from utils.db import get_db
        import traceback
        
        # Check if any session exists in MongoDB
        if settings.use_mongodb and settings.mongodb_url:
            print("🔍 [API /api/naver/status] Checking MongoDB...")
            db = get_db()
            if db is not None:
                # Count total sessions
                session_count = db.naver_sessions.count_documents({})
                print(f"🔍 [API /api/naver/status] Session count: {session_count}")
                
                if session_count > 0:
                    print(f"✅ [API /api/naver/status] Found {session_count} session(s) in MongoDB!")
                    
                    # Get most recently used session
                    try:
                        sessions_cursor = db.naver_sessions.find({}).sort("last_used", -1).limit(1)
                        sessions_list = list(sessions_cursor)
                        active_user = sessions_list[0].get('_id') if sessions_list else None
                    except Exception as sort_err:
                        print(f"⚠️ Sort error: {sort_err}, using any session")
                        active_user = None
                    
                    return {
                        'logged_in': True,
                        'message': f'{session_count}개의 세션이 저장됨',
                        'session_count': session_count,
                        'active_user': active_user
                    }
                else:
                    print("❌ [API /api/naver/status] No sessions in MongoDB")
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
async def get_naver_places(user_id: str = "default"):
    """
    Get list of places in Smart Place Center
    
    Args:
        user_id: User ID for multi-account support (default: "default")
    """
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
    user_id: str = Body("default")
):
    """
    비동기로 리뷰 로드 (30초 타임아웃 우회)
    
    즉시 task_id를 반환하고 백그라운드에서 리뷰 로드
    프론트엔드는 /tasks/{task_id}로 진행 상황 폴링
    """
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
async def get_naver_reviews(place_id: str, page: int = 1, page_size: int = 20, load_count: int = 300, user_id: str = "default"):
    """
    Get reviews for a specific place with pagination
    
    ⚠️ 주의: 100개 이상은 /reviews/load-async 사용 권장 (타임아웃 방지)
    
    User can specify how many reviews to load at once
    
    Args:
        place_id: Naver place ID
        page: Page number (starting from 1)
        page_size: Number of reviews per page (default 20)
        load_count: Total number of reviews to load (50/150/300/500/1000)
        user_id: User ID for multi-account support (default: "default")
    """
    # Set active user before calling service
    naver_service.set_active_user(user_id)
    
    return await naver_service.get_reviews(place_id, page=page, page_size=page_size, filter_type='all', load_count=load_count)


@router.post("/reviews/reply-async")
async def post_reply_async(
    place_id: str = Body(...),
    author: str = Body(...),      # 작성자
    date: str = Body(...),        # 날짜
    reply_text: str = Body(...),
    user_id: str = Body("default")
):
    """
    비동기로 답글 게시 (30초 타임아웃 우회)
    작성자 + 날짜 2중 매칭 - 가장 확실한 방법
    """
    from utils.task_manager import task_manager
    
    # Create task
    task_id = task_manager.create_task(
        task_type='reply_post',
        user_id=user_id,
        params={
            'place_id': place_id,
            'author': author,
            'date': date,
            'reply_text': reply_text
        }
    )
    
    # Start background thread
    def background_reply():
        try:
            task_manager.update_task_status(task_id, 'processing')
            task_manager.update_progress(task_id, 0, '답글 게시 중...')
            
            # 🚀 직접 selenium 함수 호출 (wrapper 우회, Lock 문제 해결)
            from services.naver_automation_selenium import naver_automation_selenium
            
            # 🚀 작성자 + 날짜 2중 매칭 (user_id도 함께 전달)
            result = naver_automation_selenium.post_reply_by_author_date(
                place_id=place_id,
                author=author,
                date=date,
                reply_text=reply_text,
                user_id=user_id  # user_id 직접 전달
            )
            
            task_manager.set_result(task_id, result)
            task_manager.update_task_status(task_id, 'completed')
            task_manager.update_progress(task_id, 1, '✅ 답글 게시 완료!')
            
        except Exception as e:
            print(f"❌ Background reply task {task_id} failed: {e}")
            import traceback
            traceback.print_exc()
            task_manager.set_error(task_id, str(e))
    
    thread = threading.Thread(target=background_reply, daemon=True)
    thread.start()
    
    return {
        'task_id': task_id,
        'message': '답글을 게시하고 있습니다.',
        'status_url': f'/api/naver/tasks/{task_id}'
    }


@router.post("/reviews/reply")
async def post_naver_reply(request: NaverReplyRequest, user_id: str = "default"):
    """
    Post a reply to a Naver review (동기 방식 - 30초 제한)
    
    ⚠️ 주의: /reviews/reply-async 사용 권장 (타임아웃 방지)
    
    Args:
        request: Reply request with place_id, review_id, and reply_text
        user_id: User ID for multi-account support (default: "default")
    """
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
async def upload_session(session_data: NaverSessionUpload):
    """
    Upload Naver session from external tool (EXE)
    
    This endpoint receives session cookies from the desktop tool
    and stores them in MongoDB for cloud usage.
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
        
        # Prepare session document
        session_doc = {
            "_id": session_data.user_id,
            "username": session_data.username,
            "cookies": session_data.cookies,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7),  # 7 days validity
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
async def list_sessions():
    """
    Get all available Naver sessions
    """
    try:
        from utils.db import get_db
        
        if not settings.use_mongodb or not settings.mongodb_url:
            return {"sessions": []}
        
        db = get_db()
        if db is None:
            return {"sessions": []}
        
        # Get all sessions
        sessions = list(db.naver_sessions.find({}, {
            "_id": 1,
            "username": 1,
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
async def switch_session(user_id: str):
    """
    Switch to a different Naver account session
    
    This sets the active session that will be used for API calls
    """
    try:
        from utils.db import get_db
        
        if not settings.use_mongodb or not settings.mongodb_url:
            raise HTTPException(status_code=500, detail="MongoDB not configured")
        
        db = get_db()
        if db is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # Check if session exists
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
        
    except Exception as e:
        print(f"❌ Session switch error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Session switch failed: {str(e)}")


@router.delete("/session")
async def delete_session(user_id: str = "default"):
    """
    Delete session from MongoDB
    """
    try:
        from utils.db import get_db
        
        if not settings.use_mongodb or not settings.mongodb_url:
            raise HTTPException(status_code=500, detail="MongoDB not configured")
        
        db = get_db()
        if db is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        result = db.naver_sessions.delete_one({"_id": user_id})
        
        if result.deleted_count > 0:
            return {
                "success": True,
                "message": "Session deleted successfully"
            }
        else:
            return {
                "success": False,
                "message": "No session found to delete"
            }
            
    except Exception as e:
        print(f"❌ Session delete error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Session delete failed: {str(e)}")



