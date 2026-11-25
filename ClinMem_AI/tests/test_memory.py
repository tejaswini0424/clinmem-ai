import pytest
from backend.database.db_operations import Store
from backend.authentication.auth import register
from backend.memory.memory_versioning import history
from backend.memory.memory_consolidation import consolidate
from backend.knowledge_graph.graph_manager import build
def test_isolation_versions(store):
 id=store.add('Diabetes evidence',source='A')
 assert store.add('Diabetes evidence',source='A')==id
 other=Store(store.factory,register(store.factory,'other','p','p'))
 assert not other.memories()
 with pytest.raises(ValueError): other.update(id,status='Archived')
 store.update(id,'Diabetes revised evidence',reason='New source reviewed')
 assert len(history(store,id))==2
 store.update(id,status='Archived');assert not store.memories(include_archived=False)
 store.update(id,status='Active');assert store.memories()[0].status=='Active'
def test_graph_consolidation(store):
 store.add('Diabetes glucose observation',source='A');store.add('Diabetes insulin observation',source='B')
 assert consolidate(store)['findings']==1
 assert 'diabetes' in build(store)
