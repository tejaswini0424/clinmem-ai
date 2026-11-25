from sqlalchemy import select
from backend.database.models import Version
def history(store,id):
 with store.factory() as s:
  store.get(s,id)
  return list(s.scalars(select(Version).where(Version.memory_id==id).order_by(Version.number)))
