import json
import os
from typing import Optional
from google.oauth2.credentials import Credentials
from config import settings


class TokenManager:
    """Manages OAuth tokens for GBP"""
    
    def __init__(self):
        self.tokens_dir = settings.tokens_dir
        os.makedirs(self.tokens_dir, exist_ok=True)
    
    def save_token(self, user_id: str, credentials: Credentials) -> None:
        """Save OAuth credentials to file"""
        token_file = os.path.join(self.tokens_dir, f"{user_id}.json")
        token_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        with open(token_file, 'w') as f:
            json.dump(token_data, f, indent=2)
    
    def load_token(self, user_id: str) -> Optional[Credentials]:
        """Load OAuth credentials from file"""
        token_file = os.path.join(self.tokens_dir, f"{user_id}.json")
        
        if not os.path.exists(token_file):
            return None
        
        with open(token_file, 'r') as f:
            token_data = json.load(f)
        
        credentials = Credentials(
            token=token_data.get('token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data.get('token_uri'),
            client_id=token_data.get('client_id'),
            client_secret=token_data.get('client_secret'),
            scopes=token_data.get('scopes')
        )
        
        return credentials
    
    def delete_token(self, user_id: str) -> bool:
        """Delete OAuth credentials"""
        token_file = os.path.join(self.tokens_dir, f"{user_id}.json")
        
        if os.path.exists(token_file):
            os.remove(token_file)
            return True
        return False
    
    def token_exists(self, user_id: str) -> bool:
        """Check if token exists for user"""
        token_file = os.path.join(self.tokens_dir, f"{user_id}.json")
        return os.path.exists(token_file)


token_manager = TokenManager()



