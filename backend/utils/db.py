"""
MongoDB Database Connection and Utilities
파일 기반 저장소를 MongoDB로 대체하여 클라우드 배포 시 데이터 영속성 확보
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from typing import Optional, Dict, Any
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Global MongoDB client
_client: Optional[MongoClient] = None
_db = None


def init_mongodb(mongodb_url: str):
    """Initialize MongoDB connection"""
    global _client, _db
    
    if not mongodb_url:
        logger.warning("⚠️ MongoDB URL not provided. Using file-based storage.")
        return False
    
    try:
        _client = MongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
        # Test connection
        _client.admin.command('ping')
        _db = _client['review_system']
        logger.info("✅ MongoDB connected successfully!")
        return True
    except ConnectionFailure as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        _client = None
        _db = None
        return False
    except Exception as e:
        logger.error(f"❌ MongoDB initialization error: {e}")
        _client = None
        _db = None
        return False


def get_db():
    """Get MongoDB database instance"""
    if _db is None:
        raise Exception("MongoDB not initialized. Call init_mongodb() first.")
    return _db


def is_mongodb_available() -> bool:
    """Check if MongoDB is available"""
    return _db is not None


# ==================== Token Management ====================

def save_token(platform: str, user_id: str, token_data: Dict[str, Any]) -> bool:
    """
    Save OAuth token to MongoDB or file
    
    Args:
        platform: 'google' or 'naver'
        user_id: User identifier
        token_data: Token data dictionary
    """
    if is_mongodb_available():
        try:
            db = get_db()
            db.tokens.update_one(
                {"platform": platform, "user_id": user_id},
                {
                    "$set": {
                        "token_data": token_data,
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            logger.info(f"✅ Token saved to MongoDB: {platform}/{user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save token to MongoDB: {e}")
            return False
    else:
        # Fallback to file-based storage
        from config import settings
        token_file = os.path.join(settings.tokens_dir, f"{platform}_{user_id}.json")
        try:
            with open(token_file, 'w', encoding='utf-8') as f:
                json.dump(token_data, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Token saved to file: {token_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save token to file: {e}")
            return False


def get_token(platform: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get OAuth token from MongoDB or file
    
    Args:
        platform: 'google' or 'naver'
        user_id: User identifier
        
    Returns:
        Token data dictionary or None
    """
    if is_mongodb_available():
        try:
            db = get_db()
            result = db.tokens.find_one({"platform": platform, "user_id": user_id})
            if result:
                logger.info(f"✅ Token retrieved from MongoDB: {platform}/{user_id}")
                return result.get("token_data")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get token from MongoDB: {e}")
            return None
    else:
        # Fallback to file-based storage
        from config import settings
        token_file = os.path.join(settings.tokens_dir, f"{platform}_{user_id}.json")
        if os.path.exists(token_file):
            try:
                with open(token_file, 'r', encoding='utf-8') as f:
                    token_data = json.load(f)
                logger.info(f"✅ Token retrieved from file: {token_file}")
                return token_data
            except Exception as e:
                logger.error(f"❌ Failed to read token from file: {e}")
                return None
        return None


def delete_token(platform: str, user_id: str) -> bool:
    """Delete OAuth token"""
    if is_mongodb_available():
        try:
            db = get_db()
            result = db.tokens.delete_one({"platform": platform, "user_id": user_id})
            logger.info(f"✅ Token deleted from MongoDB: {platform}/{user_id}")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"❌ Failed to delete token from MongoDB: {e}")
            return False
    else:
        # Fallback to file-based storage
        from config import settings
        token_file = os.path.join(settings.tokens_dir, f"{platform}_{user_id}.json")
        if os.path.exists(token_file):
            try:
                os.remove(token_file)
                logger.info(f"✅ Token file deleted: {token_file}")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to delete token file: {e}")
                return False
        return False


# ==================== Session Management (Naver) ====================

def save_naver_session(user_id: str, session_data: Dict[str, Any]) -> bool:
    """Save Naver browser session"""
    if is_mongodb_available():
        try:
            db = get_db()
            db.naver_sessions.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "session_data": session_data,
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            logger.info(f"✅ Naver session saved to MongoDB: {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save Naver session to MongoDB: {e}")
            return False
    else:
        # Fallback to file-based storage
        from config import settings
        session_file = os.path.join(settings.data_dir, "naver_sessions", f"session_{user_id}.json")
        os.makedirs(os.path.dirname(session_file), exist_ok=True)
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Naver session saved to file: {session_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save Naver session to file: {e}")
            return False


def get_naver_session(user_id: str) -> Optional[Dict[str, Any]]:
    """Get Naver browser session"""
    if is_mongodb_available():
        try:
            db = get_db()
            result = db.naver_sessions.find_one({"user_id": user_id})
            if result:
                logger.info(f"✅ Naver session retrieved from MongoDB: {user_id}")
                return result.get("session_data")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get Naver session from MongoDB: {e}")
            return None
    else:
        # Fallback to file-based storage
        from config import settings
        session_file = os.path.join(settings.data_dir, "naver_sessions", f"session_{user_id}.json")
        if os.path.exists(session_file):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                logger.info(f"✅ Naver session retrieved from file: {session_file}")
                return session_data
            except Exception as e:
                logger.error(f"❌ Failed to read Naver session from file: {e}")
                return None
        return None


# ==================== User Data ====================

def save_user_data(user_id: str, data: Dict[str, Any]) -> bool:
    """Save user-specific data"""
    if is_mongodb_available():
        try:
            db = get_db()
            db.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "data": data,
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            logger.info(f"✅ User data saved to MongoDB: {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save user data to MongoDB: {e}")
            return False
    else:
        logger.warning("⚠️ MongoDB not available. User data not saved.")
        return False


def get_user_data(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user-specific data"""
    if is_mongodb_available():
        try:
            db = get_db()
            result = db.users.find_one({"user_id": user_id})
            if result:
                return result.get("data")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get user data from MongoDB: {e}")
            return None
    else:
        return None


# ==================== Place AI Settings ====================

def get_place_ai_settings(place_id: str, google_email: str) -> Optional[Dict[str, Any]]:
    """
    Get AI settings for a specific place
    
    Args:
        place_id: Naver place ID
        google_email: Google account email
        
    Returns:
        AI settings document or None
    """
    if not is_mongodb_available():
        logger.warning("⚠️ MongoDB not available. Cannot get AI settings.")
        return None
    
    try:
        db = get_db()
        settings = db.place_ai_settings.find_one({
            "place_id": place_id,
            "google_email": google_email
        })
        if settings:
            logger.info(f"✅ AI settings retrieved for place {place_id}")
        return settings
    except Exception as e:
        logger.error(f"❌ Failed to get AI settings from MongoDB: {e}")
        return None


def save_place_ai_settings(place_id: str, google_email: str, settings: Dict[str, Any]) -> bool:
    """
    Save AI settings for a specific place
    
    Args:
        place_id: Naver place ID
        google_email: Google account email
        settings: AI settings dictionary
        
    Returns:
        True if successful, False otherwise
    """
    if not is_mongodb_available():
        logger.warning("⚠️ MongoDB not available. Cannot save AI settings.")
        return False
    
    try:
        db = get_db()
        db.place_ai_settings.update_one(
            {"place_id": place_id, "google_email": google_email},
            {
                "$set": {
                    "settings": settings,
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "place_id": place_id,
                    "google_email": google_email,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        logger.info(f"✅ AI settings saved for place {place_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to save AI settings to MongoDB: {e}")
        return False


def delete_place_ai_settings(place_id: str, google_email: str) -> bool:
    """
    Delete AI settings for a specific place
    
    Args:
        place_id: Naver place ID
        google_email: Google account email
        
    Returns:
        True if successful, False otherwise
    """
    if not is_mongodb_available():
        logger.warning("⚠️ MongoDB not available. Cannot delete AI settings.")
        return False
    
    try:
        db = get_db()
        result = db.place_ai_settings.delete_one({
            "place_id": place_id,
            "google_email": google_email
        })
        logger.info(f"✅ AI settings deleted for place {place_id}")
        return result.deleted_count > 0
    except Exception as e:
        logger.error(f"❌ Failed to delete AI settings from MongoDB: {e}")
        return False
