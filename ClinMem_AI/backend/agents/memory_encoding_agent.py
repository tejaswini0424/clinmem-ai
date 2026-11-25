from pydantic import BaseModel,Field
from typing import Literal
from backend.ingestion.document_loader import extract
from backend.ingestion.chunking import chunks
from backend.database.models import Document
from backend.database.db_operations import digest
from sqlalchemy import select
import hashlib
class KnowledgeInput(BaseModel):
 filename:str=Field(min_length=1)
 quality:Literal['High','Moderate','Limited','Unknown']='Unknown'
 source_date:str|None=None
def run(store,filename,data,quality='Unknown',source_date=None):
 spec=KnowledgeInput(filename=filename,quality=quality,source_date=source_date);pages=extract(filename,data);hash=hashlib.sha256(data).hexdigest()
 with store.factory() as s:
  old=s.scalar(select(Document).where(Document.user_id==store.user_id,Document.digest==hash))
  if old and old.status=='Completed': return {'records':0,'findings':0,'summary':'Duplicate document skipped.','ids':[]}
  if old:
   old.status='Processing';s.commit();doc_id=old.id
  else:
   doc=Document(user_id=store.user_id,filename=filename,file_type=filename.rsplit('.',1)[-1],digest=hash);s.add(doc);s.commit();doc_id=doc.id
 ids=[]
 try:
  for page,text in pages:
   for chunk in chunks(text): ids.append(store.add(chunk,source=filename,document_id=doc_id,page=page,quality=spec.quality,source_date=source_date))
  from backend.retrieval.embeddings import encode
  encode([m.content for m in store.memories(['Long-Term']) if m.id in ids])
  with store.factory() as s: s.get(Document,doc_id).status='Completed';s.commit()
 except Exception:
  with store.factory() as s: s.get(Document,doc_id).status='Failed';s.commit()
  raise
 store.add(f'Document ingested: {filename}; {len(ids)} chunks.',memory_type='Episodic',source='System event')
 return {'records':len(ids),'findings':0,'summary':f'Encoded {len(ids)} chunks.','ids':ids}
