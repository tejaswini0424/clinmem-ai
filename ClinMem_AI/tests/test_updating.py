from backend.agents.evidence_updating_agent import run
from backend.memory.memory_versioning import history
def test_conflict(store):
 a=store.add('Diabetes intervention alpha improves glucose',source='A')
 b=store.add('Diabetes intervention alpha does not improve glucose',source='B')
 assert run(store)['findings']==1
 assert all(m.status=='Conflicting' for m in store.memories(['Long-Term']))
 assert history(store,a)[0].content=='Diabetes intervention alpha improves glucose'
def test_age_not_obsolescence(store):
 store.add('Hypertension observation',source_date='2000-01-01')
 run(store);assert store.memories(['Long-Term'])[0].status=='Pending Review'

def test_synthetic_disclaimers_do_not_hide_conflict(store):
 import json
 from pathlib import Path
 records=json.loads((Path(__file__).resolve().parents[1]/'data/sample_evidence.json').read_text())
 for record in records: store.add(**record)
 result=run(store)
 assert result['findings']==1
 statuses={m.source:m.status for m in store.memories(['Long-Term','Semantic'])}
 assert statuses['Synthetic diabetes scenario A']=='Conflicting'
 assert statuses['Synthetic diabetes scenario B']=='Conflicting'
 assert statuses['Synthetic medication glossary']=='Active'
 from backend.memory.memory_consolidation import consolidate
 from backend.knowledge_graph.graph_manager import build
 consolidate(store)
 graph=build(store)
 assert 'Contradicts' in graph.edges['M1','M2']['kind']
 assert 'Related to' in graph.edges['M1','M2']['kind']
