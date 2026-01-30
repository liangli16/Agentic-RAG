# Directory: yt-agentic-rag/app/agents/tools/calendar_tool.py

"""
Calendar Tool - Schedule Meetings via Google Calendar API.

This tool allows the agent to create calendar events with:
- Automatic Google Meet link generation
- Multiple attendees
- Timezone support
- RAG-informed durations (e.g., "standard consultation = 30 min")

Uses Google Calendar API with OAuth 2.0 authentication for personal accounts.
"""

import logging
from typing import Dict, Any, List, Optional

from .base import BaseTool

logger = logging.getLogger(__name__)


class CalendarTool(BaseTool):
    """
    Tool for creating Google Calendar events.
    
    Uses Google Calendar API with OAuth 2.0 authentication.
    Works with personal Gmail accounts - no Google Workspace required.
    
    Required setup:
    1. Create a Google Cloud project
    2. Enable Google Calendar API
    3. Create OAuth 2.0 credentials (Desktop app)
    4. Download the OAuth credentials JSON
    5. Authorize the app on first use (browser opens automatically)
    """
    
    def __init__(self):
        """Initialize the Calendar tool."""
        self._service = None
        self._initialized = False
    
    @property
    def name(self) -> str:
        """Tool name matching TOOL_DEFINITIONS."""
        return "create_calendar_event"
    
    @property
    def description(self) -> str:
        """Human-readable description."""
        return "Create a calendar event/meeting on Google Calendar"
    
    def _get_service(self):
        """
        Lazily initialize and return the Calendar service.
        
        Returns:
            Google Calendar API service instance
            
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
                
                # Build the Calendar service
                self._service = build(
                    'calendar', 
                    'v3', 
                    credentials=credentials
                )
                self._initialized = True
                logger.info("Google Calendar service initialized with OAuth 2.0")
                
            except FileNotFoundError as e:
                logger.error(
                    f"OAuth credentials file not found: {e}. "
                    "Please ensure credentials/oauth_credentials.json exists. "
                    "Download from Google Cloud Console > APIs & Services > Credentials."
                )
                raise
            except Exception as e:
                logger.error(f"Failed to initialize Google Calendar service: {e}")
                raise
        
        return self._service
    
    async def execute(
        self,
        summary: str,
        start_datetime: str,
        end_datetime: str,
        description: str = "",
        attendees: Optional[List[str]] = None,
        timezone: str = "UTC",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a calendar event.
        
        Args:
            summary: Event title/summary
            start_datetime: Start time in ISO 8601 format (e.g., '2024-12-15T14:00:00')
            end_datetime: End time in ISO 8601 format (e.g., '2024-12-15T15:00:00')
            description: Optional event description
            attendees: Optional list of attendee email addresses
            timezone: Timezone for the event (default: UTC)
            **kwargs: Additional arguments (ignored)
            
        Returns:
            Dict with success status and event details or error message
        """
        # Validate required parameters
        is_valid, missing = self.validate_params(
            required=['summary', 'start_datetime', 'end_datetime'],
            provided={
                'summary': summary,
                'start_datetime': start_datetime,
                'end_datetime': end_datetime
            }
        )
        
        if not is_valid:
            return self._error_response(
                f"Missing required parameters: {', '.join(missing)}"
            )
        
        try:
            # Import here to handle case where google packages not installed
            from googleapiclient.errors import HttpError
            from ...config.settings import get_settings
            settings = get_settings()
            
            service = self._get_service()
            
            # Build event body with Google Meet conferencing
            event = {
                'summary': summary,
                'description': description or 'Scheduled via Agentic RAG Assistant',
                'start': {
                    'dateTime': start_datetime,
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end_datetime,
                    'timeZone': timezone,
                },
                # Add Google Meet video conferencing
                'conferenceData': {
                    'createRequest': {
                        'requestId': f'agentic-rag-{start_datetime.replace(":", "-").replace("T", "-")}',
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        }
                    }
                },
            }
            
            # Add other attendees if provided
            if attendees:
                attendee_list = [{'email': email} for email in attendees]
                event['attendees'] = attendee_list
            
            # Create the event with conference data support
            # Use 'primary' calendar for OAuth (user's main calendar)
            created_event = service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1,  # Required to create Meet link
                sendUpdates='all'  # Send email invitations to all attendees
            ).execute()
            
            # Extract Google Meet link if available
            meet_link = None
            conference_data = created_event.get('conferenceData')
            if conference_data:
                entry_points = conference_data.get('entryPoints', [])
                for ep in entry_points:
                    if ep.get('entryPointType') == 'video':
                        meet_link = ep.get('uri')
                        break
            
            # Get organizer email from created event
            organizer_email = created_event.get('organizer', {}).get('email', 'me')
            
            logger.info(
                f"Calendar event created successfully: "
                f"ID={created_event.get('id')}, Summary='{summary}', "
                f"Meet Link={meet_link}"
            )
            
            return self._success_response({
                "event_id": created_event.get('id'),
                "event_link": created_event.get('htmlLink'),
                "meet_link": meet_link,
                "summary": created_event.get('summary'),
                "organizer": organizer_email,
                "start": created_event.get('start'),
                "end": created_event.get('end'),
                "attendees": [
                    a.get('email') 
                    for a in created_event.get('attendees', [])
                ],
                "status": created_event.get('status')
            })
            
        except ImportError as e:
            return self._error_response(
                f"Google API packages not installed. "
                f"Run: pip install google-api-python-client google-auth. "
                f"Error: {str(e)}"
            )
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return self._error_response(
                f"Calendar API error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}", exc_info=True)
            return self._error_response(
                f"Failed to create event: {str(e)}"
            )


# Global tool instance
calendar_tool = CalendarTool()

