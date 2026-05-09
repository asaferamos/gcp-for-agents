from googleapiclient.discovery import build
from gcp_for_agents.auth import get_credentials

class SheetsClient:
    def __init__(self, credentials_path='credentials.json', token_path='token.json'):
        self.creds = get_credentials(credentials_path, token_path)
        self.service = build('sheets', 'v4', credentials=self.creds)

    def __getattr__(self, name):
        """Delegate attribute access to the underlying Google API service."""
        return getattr(self.service, name)

    def read(self, spreadsheet_id: str, range_name: str) -> list:
        """Reads values from a spreadsheet range."""
        sheet = self.service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                    range=range_name).execute()
        values = result.get('values', [])
        return values

    def update(self, spreadsheet_id: str, range_name: str, values: list, clear: bool = False):
        """Updates a spreadsheet range with new values.
        If clear is True, it clears the entire sheet and inserts data starting from A1.
        """
        if clear:
            sheet_name = range_name.split('!')[0] if '!' in range_name else range_name
            self.service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=sheet_name
            ).execute()
            range_name = f"{sheet_name}!A1"

        body = {
            'values': values
        }
        result = self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption="RAW", body=body).execute()
        return result
