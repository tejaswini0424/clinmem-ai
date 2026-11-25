from datetime import datetime,timedelta,timezone
from sqlalchemy import delete
from backend.database.models import Memory,Evidence,Version
def clear_working(store,session_id):
 with store.factory() as s:
  ids=[m.id for m in store.memories(['Working']) if m.session_id==session_id]
  if ids:
   s.execute(delete(Evidence).where(Evidence.memory_id.in_(ids)));s.execute(delete(Version).where(Version.memory_id.in_(ids)));s.execute(delete(Memory).where(Memory.id.in_(ids),Memory.user_id==store.user_id));s.commit()
def expire_context(store):
 now=datetime.now(timezone.utc)
 for m in store.memories(['Short-Term']):
  if m.status!='Archived' and (now-datetime.fromisoformat(m.created))>timedelta(hours=24): store.update(m.id,status='Archived',reason='24-hour context retention')
