# GCP for Agents

`gcp-for-agents` is a Python library designed to easily connect to Google Workspace APIs, starting with Google Docs and Google Sheets. 
This library expects that the application using it already handles the Google OAuth2 login flow and provides the credentials.

## Components Implemented

1. **Google Docs Wrapper (`gcp_for_agents.DocsClient`)**: 
   - `read(document_id)`: Fetches the document and extracts the text (including basic paragraphs and tables).
   - `update(document_id, text, append=True, clear=False)`: Adds text to the document. It supports deleting the previous content via the `clear=True` flag, and choosing whether to insert at the beginning or append to the end.

2. **Google Sheets Wrapper (`gcp_for_agents.SheetsClient`)**: 
   - `read(spreadsheet_id, range_name)`: Returns the values of the cells in the specified range.
   - `update(spreadsheet_id, range_name, values)`: Updates the values in the specified range with a new 2D array of data.

## How to use

First, install the package:
```bash
pip install -e .
```

### Python Library Usage

When you instantiate a client (or call `login()`), the library will automatically look for `token.json` in the current directory. 
If it doesn't exist or is expired, it will read `credentials.json` and open the Google Authorization flow in the browser, subsequently saving `token.json` for future runs.

```python
from gcp_for_agents import DocsClient, SheetsClient, login

# Optional: Force a login/re-login to update the token
# login(credentials_path="credentials.json", token_path="token.json")

# Instantiating the client handles auth automatically.
# It uses credentials.json to log in and saves to token.json
docs = DocsClient(credentials_path="credentials.json", token_path="token.json")

# Read a document
content = docs.read("1YOUR_DOC_ID_HERE")
print(content)

# Update a document (clear everything and add new text)
docs.update("1YOUR_DOC_ID_HERE", "Hello World", clear=True)

# Sheets Example
sheets = SheetsClient(credentials_path="credentials.json", token_path="token.json")
values = sheets.read("1YOUR_SHEET_ID_HERE", "Sheet1!A1:B2")

# Update a sheet (with clear=True, it will erase the entire sheet and insert data at A1)
sheets.update("1YOUR_SHEET_ID_HERE", "Sheet1", [["Name", "Age"], ["John", "30"]], clear=True)
```
