import re
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

    def update(self, document_id: str, text: str, append: bool = True, clear: bool = False, markdown: bool = False):
        """Updates a document. 
        If clear is True, it deletes all content before inserting.
        If append is True (and clear is False), it appends to the end.
        Otherwise it inserts at the beginning (index 1).
        If markdown is True, it parses basic markdown formatting.
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
            insert_index = 1
            if append and not clear:
                doc = self.service.documents().get(documentId=document_id).execute()
                content = doc.get('body').get('content')
                last_element = content[-1]
                insert_index = last_element.get('endIndex') - 1
            
            if markdown:
                clean_text, formatting = self._parse_markdown(text)
                text_to_insert = clean_text
            else:
                text_to_insert = text + '\n'
                formatting = []

            requests.append({
                'insertText': {
                    'location': {
                        'index': insert_index,
                    },
                    'text': text_to_insert
                }
            })

            for fmt in formatting:
                fmt_range = {
                    'startIndex': insert_index + fmt['range']['startIndex'],
                    'endIndex': insert_index + fmt['range']['endIndex']
                }
                
                if fmt['type'].startswith('HEADING_') or fmt['type'] == 'TITLE':
                    requests.append({
                        'updateParagraphStyle': {
                            'range': fmt_range,
                            'paragraphStyle': {'namedStyleType': fmt['type']},
                            'fields': 'namedStyleType'
                        }
                    })
                else:
                    text_style = {}
                    if fmt['type'] == 'BOLD': text_style['bold'] = True
                    if fmt['type'] == 'ITALIC': text_style['italic'] = True
                    if fmt['type'] == 'CODE': text_style['weightedFontFamily'] = {'fontFamily': 'Courier New'}
                    
                    fields = []
                    if 'bold' in text_style: fields.append('bold')
                    if 'italic' in text_style: fields.append('italic')
                    if 'weightedFontFamily' in text_style: fields.append('weightedFontFamily')
                    
                    requests.append({
                        'updateTextStyle': {
                            'range': fmt_range,
                            'textStyle': text_style,
                            'fields': ','.join(fields)
                        }
                    })

        if requests:
            result = self.service.documents().batchUpdate(
                documentId=document_id, body={'requests': requests}).execute()
            return result
        return None

    def _parse_markdown(self, text: str):
        """Parses basic markdown and returns cleaned text and formatting requests."""
        lines = text.split('\n')
        clean_text = ""
        style_requests = []
        current_index = 0
        
        for line in lines:
            # Handle Headers
            header_level = 0
            is_title = False
            if line.startswith('#'):
                # Check for Title pattern: # **Text**
                title_match = re.match(r'^#\s*\*\*(.*)\*\*\s*$', line)
                if title_match:
                    is_title = True
                    line = title_match.group(1)
                else:
                    match = re.match(r'^(#+)\s*(.*)', line)
                    if match:
                        header_level = len(match.group(1))
                        line = match.group(2)
            
            # Handle inline styles (Bold, Italic, Code)
            cleaned_line = ""
            line_styles = []
            
            i = 0
            while i < len(line):
                # Bold **
                if line.startswith('**', i):
                    end = line.find('**', i + 2)
                    if end != -1:
                        content = line[i+2:end]
                        line_styles.append({'type': 'BOLD', 'start': len(cleaned_line), 'end': len(cleaned_line) + len(content)})
                        cleaned_line += content
                        i = end + 2
                        continue
                # Italic *
                elif line.startswith('*', i):
                    end = line.find('*', i + 1)
                    if end != -1:
                        content = line[i+1:end]
                        line_styles.append({'type': 'ITALIC', 'start': len(cleaned_line), 'end': len(cleaned_line) + len(content)})
                        cleaned_line += content
                        i = end + 1
                        continue
                # Code `
                elif line.startswith('`', i):
                    end = line.find('`', i + 1)
                    if end != -1:
                        content = line[i+1:end]
                        line_styles.append({'type': 'CODE', 'start': len(cleaned_line), 'end': len(cleaned_line) + len(content)})
                        cleaned_line += content
                        i = end + 1
                        continue
                
                cleaned_line += line[i]
                i += 1
            
            # Record style requests relative to current_index
            for style in line_styles:
                style_requests.append({
                    'type': style['type'],
                    'range': {
                        'startIndex': current_index + style['start'],
                        'endIndex': current_index + style['end']
                    }
                })
            
            if is_title:
                style_requests.append({
                    'type': 'TITLE',
                    'range': {
                        'startIndex': current_index,
                        'endIndex': current_index + len(cleaned_line)
                    }
                })
            elif 0 < header_level <= 5:
                style_requests.append({
                    'type': f'HEADING_{header_level}',
                    'range': {
                        'startIndex': current_index,
                        'endIndex': current_index + len(cleaned_line)
                    }
                })
            
            clean_text += cleaned_line + '\n'
            current_index += len(cleaned_line) + 1 # +1 for \n
            
        return clean_text, style_requests
