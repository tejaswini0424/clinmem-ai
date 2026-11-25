import pytest
from io import BytesIO
from docx import Document
from backend.ingestion.document_loader import extract
from backend.agents.memory_encoding_agent import run
def test_ingestion(store):
 result=run(store,'sample.txt',b'Diabetes glucose evidence')
 assert result['records']==1
 assert run(store,'sample.txt',b'Diabetes glucose evidence')['records']==0
 assert store.memories(['Long-Term'])[0].category=='Condition'
def test_formats():
 assert extract('x.csv',b'topic,value\ndiabetes,glucose')[0][0] is None
 doc=Document();doc.add_paragraph('Diabetes evidence');buffer=BytesIO();doc.save(buffer)
 assert 'Diabetes' in extract('x.docx',buffer.getvalue())[0][1]
 for filename,data in [('x.exe',b'hi'),('x.txt',b''),('x.pdf',b'broken')]:
  with pytest.raises(ValueError): extract(filename,data)
