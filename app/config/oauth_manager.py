# Copyright 2024
# Directory: yt-agentic-rag/app/config/oauth_manager.py

"""
OAuth 2.0 Token Manager for Google APIs.

Handles the OAuth flow and token persistence for personal Google accounts.
This replaces the service account + domain-wide delegation approach,
allowing the app to work with personal Gmail accounts.
"""

import os
import logging
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

logger = logging.getLogger(__name__)

# OAuth scopes needed for Calendar and Gmail
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.send'
]


class OAuthManager:
    """Manages OAuth 2.0 authentication for Google APIs."""
    
    def __init__(
        self, 
        credentials_path: str = "credentials/oauth_credentials.json",
        token_path: str = "credentials/token.json"
    ):
        """
        Initialize OAuth manager.
        
        Args:
            credentials_path: Path to OAuth client credentials JSON
            token_path: Path to store/load the user token
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self._credentials: Optional[Credentials] = None
    
    def get_credentials(self) -> Credentials:
        """
        Get valid credentials, handling token refresh and new authorization.
        
        This method will:
        1. Load existing token if available
        2. Refresh it if expired
        3. Trigger OAuth flow if no valid token exists (opens browser)
        
        Returns:
            Valid Google OAuth2 credentials
            
        Raises:
            FileNotFoundError: If oauth_credentials.json is missing
            Exception: If authorization fails
        """
        # Load existing token if available
        if os.path.exists(self.token_path):
            logger.info(f"Loading existing token from {self.token_path}")
            self._credentials = Credentials.from_authorized_user_file(
                self.token_path, 
                SCOPES
            )
        
        # Refresh token if expired, or do new OAuth flow
        if not self._credentials or not self._credentials.valid:
            if self._credentials and self._credentials.expired and self._credentials.refresh_token:
                logger.info("Refreshing expired token...")
                try:
                    self._credentials.refresh(Request())
                    logger.info("Token refreshed successfully")
                except Exception as e:
                    logger.warning(f"Token refresh failed: {e}. Starting new OAuth flow...")
                    self._credentials = None
            
            # Need to do full OAuth flow if refresh failed or no token exists
            if not self._credentials:
                logger.info("Starting OAuth authorization flow...")
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"OAuth credentials not found at {self.credentials_path}. "
                        "Download from Google Cloud Console (APIs & Services > Credentials)."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, 
                    SCOPES
                )
                # This will open a browser window for user to authorize
                self._credentials = flow.run_local_server(port=0)
                logger.info("Authorization successful!")
            
            # Save the credentials for future use
            self._save_token()
        
        return self._credentials
    
    def _save_token(self):
        """Save the credentials to token file for persistence."""
        # Ensure credentials directory exists
        Path(self.token_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.token_path, 'w') as token_file:
            token_file.write(self._credentials.to_json())
        logger.info(f"Token saved to {self.token_path}")
    
    def clear_token(self):
        """Clear saved token (useful for testing or re-authorization)."""
        if os.path.exists(self.token_path):
            os.remove(self.token_path)
            logger.info(f"Token cleared from {self.token_path}")
        self._credentials = None


# Global singleton instance
_oauth_manager: Optional[OAuthManager] = None


def get_oauth_manager() -> OAuthManager:
    """
    Get global OAuth manager instance.
    
    Returns:
        Singleton OAuthManager instance
    """
    global _oauth_manager
    if _oauth_manager is None:
        from .settings import get_settings
        settings = get_settings()
        _oauth_manager = OAuthManager(
            credentials_path=settings.google_oauth_credentials_path,
            token_path=settings.google_token_path
        )
    return _oauth_manager
