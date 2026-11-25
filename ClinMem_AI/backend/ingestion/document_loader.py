from io import BytesIO,StringIO
from pathlib import Path
import csv
def extract(filename,data):
 if not data or len(data)>20*1024*1024: raise ValueError('File must be non-empty and at most 20 MB.')
 suffix=Path(filename).suffix.lower()
 try:
  if suffix=='.pdf':
   from pypdf import PdfReader
   pages=[(i+1,p.extract_text() or '') for i,p in enumerate(PdfReader(BytesIO(data)).pages)]
  elif suffix=='.docx':
   from docx import Document
   d=Document(BytesIO(data));pages=[(None,'\n'.join([p.text for p in d.paragraphs]+[' | '.join(c.text for c in row.cells) for t in d.tables for row in t.rows]))]
  elif suffix=='.txt': pages=[(None,data.decode('utf-8-sig'))]
  elif suffix=='.csv': pages=[(None,' | '.join(row)) for row in csv.reader(StringIO(data.decode('utf-8-sig'))) if any(row)]
  else: raise ValueError('Supported formats: PDF, DOCX, TXT, CSV.')
 except Exception as exc: raise ValueError(f'Cannot extract document: {exc}') from exc
 if not any(t.strip() for _,t in pages): raise ValueError('No readable text. Scanned PDFs require external OCR.')
 return pages
