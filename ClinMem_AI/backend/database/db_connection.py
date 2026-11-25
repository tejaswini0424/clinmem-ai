from sqlalchemy import create_engine,event
from sqlalchemy.orm import sessionmaker
from config.settings import DATABASE_URL
from .models import Base
def connect(url=DATABASE_URL):
 sqlite=url.startswith('sqlite:')
 engine=create_engine(url,connect_args={'check_same_thread':False} if sqlite else {},pool_pre_ping=True)
 if sqlite:
  @event.listens_for(engine,'connect')
  def foreign_keys(dbapi, record): dbapi.execute('PRAGMA foreign_keys=ON')
 Base.metadata.create_all(engine)
 return sessionmaker(engine,expire_on_commit=False)
