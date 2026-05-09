import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/calendar'
]

def get_credentials(credentials_path='credentials.json', token_path='token.json'):
    """Gets valid user credentials from storage or initiates login."""
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"Credentials file '{credentials_path}' not found. "
                    "Please provide a valid OAuth2 client secrets file."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    return creds

def login(credentials_path='credentials.json', token_path='token.json'):
    """Forces a login/re-login and saves the token."""
    if os.path.exists(token_path):
        os.remove(token_path)
    print("Initiating login flow...")
    creds = get_credentials(credentials_path, token_path)
    print(f"Login successful. Token saved to {token_path}")
    return creds
