from backend.reports.pdf_generator import generate
from backend.ingestion.document_loader import extract
def test_pdf():
 data=generate('ClinMem AI',[('Evidence','Diabetes <source> & uncertainties')])
 assert data.startswith(b'%PDF')
 pages=extract('report.pdf',data)
 assert 'Diabetes' in pages[0][1]
