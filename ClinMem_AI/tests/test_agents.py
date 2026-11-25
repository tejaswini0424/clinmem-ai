from backend.orchestration.orchestrator import Orchestrator
from backend.database.models import AgentLog
from sqlalchemy import select
def test_orchestration(store):
 orch=Orchestrator(store)
 orch.ingest(filename='test.txt',data=b'Diabetes glucose fictional evidence')
 answer,results=orch.ask('diabetes glucose')
 assert results and '[1]' in answer
 assert not store.memories(['Working'])
 assert store.memories(['Short-Term'])
 with store.factory() as s: assert all(l.status=='Completed' for l in s.scalars(select(AgentLog)))
def test_failure_isolation(store):
 orch=Orchestrator(store)
 def fail(store): raise ValueError('recoverable demonstration failure')
 assert 'error' in orch.execute('Test failure',fail)
 answer,results=orch.ask('No records')
 assert 'unavailable' in answer
