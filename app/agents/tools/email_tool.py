# Directory: yt-agentic-rag/app/agents/tools/email_tool.py

"""
Email Tool - Send Emails via Gmail API.

This tool allows the agent to send emails with:
- Plain text body
- Custom subject lines
- Sent from the authenticated user's email

Uses Gmail API with OAuth 2.0 authentication for personal accounts.
"""

import logging
import base64
from typing import Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .base import BaseTool

logger = logging.getLogger(__name__)


class EmailTool(BaseTool):
    """
    Tool for sending emails via Gmail API.
    
    Uses Gmail API with OAuth 2.0 authentication.
    Works with personal Gmail accounts - no Google Workspace required.
    
    Required setup:
    1. Create a Google Cloud project
    2. Enable Gmail API
    3. Create OAuth 2.0 credentials (Desktop app)
    4. Download the OAuth credentials JSON
    5. Authorize the app on first use (browser opens automatically)
    """
    
    def __init__(self):
        """Initialize the Email tool."""
        self._service = None
        self._initialized = False
    
    @property
    def name(self) -> str:
        """Tool name matching TOOL_DEFINITIONS."""
        return "send_email"
    
    @property
    def description(self) -> str:
        """Human-readable description."""
        return "Send an email via Gmail"
    
    def _get_service(self):
        """
        Lazily initialize and return the Gmail service.
        
        Returns:
            Gmail API service instance
            
        Raises:
            Exception: If credentials are not configured or invalid
        """
        if not self._initialized:
            try:
                # Import here to avoid issues if google packages not installed
                from googleapiclient.discovery import build
                
                # Import OAuth manager
                from ...config.oauth_manager import get_oauth_manager
                
                # Get OAuth credentials (may trigger browser auth on first run)
                oauth_manager = get_oauth_manager()
                credentials = oauth_manager.get_credentials()
                
                # Build the Gmail service
                self._service = build(
                    'gmail', 
                    'v1', 
                    credentials=credentials
                )
                self._initialized = True
                logger.info("Gmail service initialized with OAuth 2.0")
                
            except FileNotFoundError as e:
                logger.error(
                    f"OAuth credentials file not found: {e}. "
                    "Please ensure credentials/oauth_credentials.json exists. "
                    "Download from Google Cloud Console > APIs & Services > Credentials."
                )
                raise
            except Exception as e:
                logger.error(f"Failed to initialize Gmail service: {e}")
                raise
        
        return self._service
    
    async def execute(
        self,
        to: str,
        subject: str,
        body: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send an email.
        
        Args:
            to: Recipient email address
            subject: Email subject line
            body: Email body content (plain text)
            **kwargs: Additional arguments (ignored)
            
        Returns:
            Dict with success status and message details or error
        """
        # Validate required parameters
        is_valid, missing = self.validate_params(
            required=['to', 'subject', 'body'],
            provided={'to': to, 'subject': subject, 'body': body}
        )
        
        if not is_valid:
            return self._error_response(
                f"Missing required parameters: {', '.join(missing)}"
            )
        
        try:
            # Import here to handle case where google packages not installed
            from googleapiclient.errors import HttpError
            
            service = self._get_service()
            
            # Create email message (from field will be set automatically by Gmail API)
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            # Attach the body as plain text
            message.attach(MIMEText(body, 'plain'))
            
            # Encode message to base64 for Gmail API
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')
            
            # Send the email (userId='me' means the authenticated user)
            sent_message = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(
                f"Email sent successfully: "
                f"ID={sent_message.get('id')}, To='{to}', Subject='{subject}'"
            )
            
            # Get user's profile to get the 'from' email
            try:
                profile = service.users().getProfile(userId='me').execute()
                from_email = profile.get('emailAddress', 'me')
            except:
                from_email = 'me'
            
            return self._success_response({
                "message_id": sent_message.get('id'),
                "thread_id": sent_message.get('threadId'),
                "to": to,
                "subject": subject,
                "from": from_email,
                "labels": sent_message.get('labelIds', [])
            })
            
        except ImportError as e:
            return self._error_response(
                f"Google API packages not installed. "
                f"Run: pip install google-api-python-client google-auth. "
                f"Error: {str(e)}"
            )
        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            return self._error_response(
                f"Gmail API error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to send email: {e}", exc_info=True)
            return self._error_response(
                f"Failed to send email: {str(e)}"
            )


# Global tool instance
email_tool = EmailTool()

