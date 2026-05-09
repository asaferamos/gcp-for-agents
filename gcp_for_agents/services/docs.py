from googleapiclient.discovery import build
from gcp_for_agents.auth import get_credentials

class DocsClient:
    def __init__(self, credentials_path='credentials.json', token_path='token.json'):
        self.creds = get_credentials(credentials_path, token_path)
        self.service = build('docs', 'v1', credentials=self.creds)

    def __getattr__(self, name):
        """Delegate attribute access to the underlying Google API service."""
        return getattr(self.service, name)

    def read(self, document_id: str) -> str:
        """Reads the content of a document and returns it as a string."""
        doc = self.service.documents().get(documentId=document_id).execute()
        return self._extract_text(doc.get('body', {}).get('content', []))

    def _extract_text(self, elements: list) -> str:
        text = ''
        for element in elements:
            if 'paragraph' in element:
                elements_in_para = element.get('paragraph').get('elements')
                for elem in elements_in_para:
                    if 'textRun' in elem:
                        text += elem.get('textRun').get('content')
            elif 'table' in element:
                table = element.get('table')
                for row in table.get('tableRows'):
                    for cell in row.get('tableCells'):
                        text += self._extract_text(cell.get('content'))
            elif 'tableOfContents' in element:
                text += self._extract_text(element.get('tableOfContents').get('content'))
        return text

    def update(self, document_id: str, text: str, append: bool = True, clear: bool = False):
        """Updates a document. 
        If clear is True, it deletes all content before inserting.
        If append is True (and clear is False), it appends to the end.
        Otherwise it inserts at the beginning (index 1).
        """
        requests = []
        
        if clear:
            doc = self.service.documents().get(documentId=document_id).execute()
            content = doc.get('body').get('content')
            if content:
                last_element = content[-1]
                end_index = last_element.get('endIndex') - 1
                if end_index > 1:
                    requests.append({
                        'deleteContentRange': {
                            'range': {
                                'startIndex': 1,
                                'endIndex': end_index
                            }
                        }
                    })
        
        if text:
            if append and not clear:
                doc = self.service.documents().get(documentId=document_id).execute()
                content = doc.get('body').get('content')
                last_element = content[-1]
                insert_index = last_element.get('endIndex') - 1
                
                requests.append({
                    'insertText': {
                        'location': {
                            'index': insert_index,
                        },
                        'text': text + '\n'
                    }
                })
            else:
                requests.append({
                    'insertText': {
                        'location': {
                            'index': 1,
                        },
                        'text': text + '\n'
                    }
                })

        if requests:
            result = self.service.documents().batchUpdate(
                documentId=document_id, body={'requests': requests}).execute()
            return result
        return None
