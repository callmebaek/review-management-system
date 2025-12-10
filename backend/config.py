from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from pathlib import Path
from dotenv import load_dotenv

# Get the directory where this config.py file is located
BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / ".env"

# Load .env file explicitly
load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore"
    )
    
    # Server Settings
    backend_port: int = 8000
    frontend_port: int = 5173
    
    # Google Business Profile OAuth
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"  # Fast & cost-effective model
    
    # MongoDB
    mongodb_url: Optional[str] = None
    use_mongodb: bool = False  # Set to True for production
    
    # Naver Settings (Stage 2)
    naver_rate_limit_delay: int = 3
    
    # Mock Data Settings
    use_mock_data: bool = False  # Set to False when real API is available
    use_mock_gbp: bool = True  # GBP Mock (quota issue)
    use_mock_naver: bool = False  # Naver Real (using sync API)
    
    # Paths
    data_dir: str = "data"
    tokens_dir: str = "data/tokens"
    prompts_file: str = "data/prompts.json"
    stores_file: str = "data/stores.json"


settings = Settings()

# Debug: Print loaded settings
print("=" * 50)
print("DEBUG: Settings loaded")
print(f"GOOGLE_CLIENT_ID: {settings.google_client_id[:20] if settings.google_client_id else 'None'}...")
print(f"GOOGLE_CLIENT_SECRET: {settings.google_client_secret[:10] if settings.google_client_secret else 'None'}...")
print(f"OPENAI_API_KEY: {settings.openai_api_key[:20] if settings.openai_api_key else 'None'}...")
print(f"USE_MOCK_GBP: {settings.use_mock_gbp}")
print(f"USE_MOCK_NAVER: {settings.use_mock_naver}")
print("=" * 50)

# Create necessary directories
os.makedirs(settings.data_dir, exist_ok=True)
os.makedirs(settings.tokens_dir, exist_ok=True)



