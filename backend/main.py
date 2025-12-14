from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
import uvicorn
import logging
import sys
import asyncio
import os

# Fix for Windows + Python 3.13 + Playwright asyncio issue
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    print("🔧 Windows asyncio policy set to WindowsSelectorEventLoopPolicy")

logger = logging.getLogger("uvicorn")

app = FastAPI(
    title="Review Management System",
    description="Manage Google Business Profile and Naver Place reviews with AI-powered replies",
    version="1.0.0"
)

# MongoDB initialization
if settings.use_mongodb and settings.mongodb_url:
    from utils.db import init_mongodb
    mongodb_connected = init_mongodb(settings.mongodb_url)
    if mongodb_connected:
        print("✅ MongoDB 연결 성공!")
    else:
        print("⚠️ MongoDB 연결 실패. 파일 기반 저장소 사용.")
else:
    print("ℹ️ MongoDB 사용 안 함. 파일 기반 저장소 사용.")

# CORS configuration
# 프로덕션과 로컬 모두 지원
allowed_origins = [
    f"http://localhost:{settings.frontend_port}",
    "http://localhost:5173",
    "http://localhost:5174",  # Added for when port 5173 is busy
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    # 🔥 Vercel 프로덕션 도메인 명시적 추가
    "https://review-management-system-ivory.vercel.app",
]

# 프로덕션 환경의 프론트엔드 URL 추가
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)
    print(f"✅ CORS: 프로덕션 프론트엔드 추가 - {frontend_url}")

# Vercel 자동 배포 URL 패턴 지원
if os.getenv("VERCEL_URL"):
    vercel_url = f"https://{os.getenv('VERCEL_URL')}"
    allowed_origins.append(vercel_url)
    print(f"✅ CORS: Vercel URL 추가 - {vercel_url}")

print(f"🌐 CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # 🔥 Vercel 와일드카드 지원 (regex 패턴)
    allow_origin_regex=r"https://.*\.vercel\.app$"
)


@app.get("/")
async def root():
    return {
        "message": "Review Management System API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    # Debug: Return actual values
    return {
        "status": "healthy",
        "gbp_configured": bool(settings.google_client_id and settings.google_client_secret),
        "openai_configured": bool(settings.openai_api_key),
        "debug": {
            "google_client_id_exists": bool(settings.google_client_id),
            "google_client_secret_exists": bool(settings.google_client_secret),
            "openai_api_key_exists": bool(settings.openai_api_key),
            "google_client_id_preview": settings.google_client_id[:30] if settings.google_client_id else None,
            "google_client_secret_preview": settings.google_client_secret[:10] if settings.google_client_secret else None,
            "openai_api_key_preview": settings.openai_api_key[:30] if settings.openai_api_key else None
        }
    }


# Import and include routers
from api.routes import auth, gbp, reviews, naver
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(gbp.router, prefix="/api/gbp", tags=["Google Business Profile"])
app.include_router(naver.router, prefix="/api/naver", tags=["Naver Place"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["Reviews"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.backend_port,
        reload=True
    )

