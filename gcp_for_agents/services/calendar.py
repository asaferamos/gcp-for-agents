from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from gcp_for_agents.auth import get_credentials

class CalendarClient:
    def __init__(self, credentials_path='credentials.json', token_path='token.json'):
        self.creds = get_credentials(credentials_path, token_path)
        self.service = build('calendar', 'v3', credentials=self.creds)

    def __getattr__(self, name):
        """Delegate attribute access to the underlying Google API service."""
        return getattr(self.service, name)

    def list_last_week_events(self, calendar_id='primary'):
        """Lists events that happened in the last week."""
        now = datetime.now(timezone.utc)
        last_week = now - timedelta(days=7)
        
        # Format as ISO string and ensure 'Z' suffix
        start_date = last_week.isoformat().replace('+00:00', 'Z')
        end_date = now.isoformat().replace('+00:00', 'Z')
        
        return self.list_events_between_dates(
            start_date=start_date,
            end_date=end_date,
            calendar_id=calendar_id
        )

    def list_events_between_dates(self, start_date, end_date, calendar_id='primary'):
        """
        Lists events between two dates.
        Dates should be in RFC3339 format (e.g., '2023-10-27T00:00:00Z').
        """
        events_result = self.service.events().list(
            calendarId=calendar_id,
            timeMin=start_date,
            timeMax=end_date,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return [self._format_event(event) for event in events]

    def _format_event(self, event):
        """Formats a Google Calendar event into the desired dictionary structure."""
        start = event.get('start', {})
        # date for all-day events, dateTime for regular events
        event_date = start.get('dateTime') or start.get('date')
        
        attendees = []
        for attendee in event.get('attendees', []):
            attendees.append({
                'email': attendee.get('email'),
                'status': attendee.get('responseStatus')
            })
            
        return {
            'date': event_date,
            'name': event.get('summary'),
            'description': event.get('description'),
            'attendees': attendees,
            'related_documents': event.get('attachments', [])
        }
