import hashlib,json
from sqlalchemy import select
from backend.database.models import Memory,Evidence,Version,now
def digest(text): return hashlib.sha256(' '.join(text.lower().split()).encode()).hexdigest()
class Store:
 def __init__(self,factory,user_id): self.factory=factory;self.user_id=user_id
 def memories(self,types=None,include_archived=True):
  with self.factory() as s:
   q=select(Memory).where(Memory.user_id==self.user_id)
   if types: q=q.where(Memory.memory_type.in_(types))
   if not include_archived: q=q.where(Memory.status!='Archived')
   return list(s.scalars(q))
 def get(self,s,id):
  m=s.scalar(select(Memory).where(Memory.id==id,Memory.user_id==self.user_id))
  if not m: raise ValueError('Memory unavailable.')
  return m
 def add(self,content,**meta):
  from backend.ingestion.text_processor import clean,entities,category
  content=clean(content)
  if not content: raise ValueError('Empty memory.')
  with self.factory() as s:
   kind=meta.get('memory_type','Long-Term')
   existing=s.scalar(select(Memory).where(Memory.user_id==self.user_id,Memory.digest==digest(content),Memory.memory_type==kind,Memory.source==meta.get('source'),Memory.document_id==meta.get('document_id')))
   if existing: return existing.id
   m=Memory(user_id=self.user_id,content=content,digest=digest(content),entities=json.dumps(entities(content)),category=category(content),**meta);s.add(m);s.flush()
   s.add(Evidence(memory_id=m.id,source=m.source,source_date=m.source_date,description=content,quality=m.quality));s.add(Version(memory_id=m.id,number=1,previous='',content=content,reason='Created'));s.commit();return m.id
 def update(self,id,content=None,status=None,reason='Human review'):
  from config.settings import STATUSES
  if status and status not in STATUSES: raise ValueError('Invalid status')
  if content is not None and not content.strip(): raise ValueError('Empty content')
  with self.factory() as s:
   m=self.get(s,id);old=m.content;old_status=m.status
   if content is not None:
    from backend.ingestion.text_processor import entities,category
    m.content=content.strip();m.digest=digest(m.content);m.entities=json.dumps(entities(m.content));m.category=category(m.content)
   m.status=status or 'Recently Updated';m.version+=1;m.updated=now()
   s.add(Version(memory_id=id,number=m.version,previous=old,content=m.content,reason=f'{reason}; status {old_status} → {m.status}'));s.commit()
 def link(self,a,b,kind,evidence):
  from backend.database.models import Relationship
  with self.factory() as s:
   self.get(s,a);self.get(s,b)
   if not s.scalar(select(Relationship).where(Relationship.source_id==a,Relationship.target_id==b,Relationship.kind==kind)):
    s.add(Relationship(source_id=a,target_id=b,kind=kind,evidence=evidence));s.commit()
