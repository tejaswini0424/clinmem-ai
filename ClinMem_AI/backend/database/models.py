from sqlalchemy import Column,Integer,String,Text,ForeignKey,Float,UniqueConstraint
from sqlalchemy.orm import declarative_base
from datetime import datetime,timezone
Base=declarative_base()
def now(): return datetime.now(timezone.utc).isoformat()
class User(Base):
 __tablename__='users'
 id=Column(Integer,primary_key=True);username=Column(String,unique=True,nullable=False);password_hash=Column(String,nullable=False);created=Column(String,default=now)
class Document(Base):
 __tablename__='documents'
 id=Column(Integer,primary_key=True);user_id=Column(Integer,ForeignKey('users.id'),nullable=False);filename=Column(String);file_type=Column(String);uploaded=Column(String,default=now);status=Column(String,default='Processing');digest=Column(String)
class Memory(Base):
 __tablename__='memories'
 id=Column(Integer,primary_key=True);user_id=Column(Integer,ForeignKey('users.id'),nullable=False);content=Column(Text);memory_type=Column(String,default='Long-Term');category=Column(String,default='General');document_id=Column(Integer,ForeignKey('documents.id'));page=Column(Integer);created=Column(String,default=now);updated=Column(String,default=now);version=Column(Integer,default=1);status=Column(String,default='Active');quality=Column(String,default='Unknown');source=Column(String);source_date=Column(String);source_type=Column(String,default='Uploaded document');entities=Column(Text,default='[]');digest=Column(String);session_id=Column(String);expires=Column(String)
class Relationship(Base):
 __tablename__='memory_relationships'
 id=Column(Integer,primary_key=True);source_id=Column(Integer,ForeignKey('memories.id'));target_id=Column(Integer,ForeignKey('memories.id'));kind=Column(String);evidence=Column(Text)
 __table_args__=(UniqueConstraint('source_id','target_id','kind'),)
class Version(Base):
 __tablename__='memory_versions'
 id=Column(Integer,primary_key=True);memory_id=Column(Integer,ForeignKey('memories.id'));number=Column(Integer);previous=Column(Text);content=Column(Text);reason=Column(String);date=Column(String,default=now)
class AgentLog(Base):
 __tablename__='agent_logs'
 id=Column(Integer,primary_key=True);user_id=Column(Integer,ForeignKey('users.id'));agent=Column(String);status=Column(String);duration=Column(Float);records=Column(Integer,default=0);findings=Column(Integer,default=0);summary=Column(Text);input_summary=Column(Text);date=Column(String,default=now)
class Evidence(Base):
 __tablename__='evidence_records'
 id=Column(Integer,primary_key=True);memory_id=Column(Integer,ForeignKey('memories.id'));source=Column(String);source_date=Column(String);description=Column(Text);quality=Column(String);verification=Column(String,default='Unverified')
class Analysis(Base):
 __tablename__='analysis_history'
 id=Column(Integer,primary_key=True);user_id=Column(Integer,ForeignKey('users.id'));query=Column(Text);answer=Column(Text);memory_ids=Column(Text);date=Column(String,default=now)
