import json,networkx as nx
from sqlalchemy import select
from backend.database.models import Relationship
def build(store):
 g=nx.Graph();rows=store.memories(['Long-Term','Semantic']);ids={m.id for m in rows}
 for m in rows:
  g.add_node(f'M{m.id}',label=f'Memory {m.id}',category=m.category,source=m.source,updated=m.updated)
  for entity in json.loads(m.entities):
   g.add_node(entity,label=entity,category='Extracted concept');g.add_edge(f'M{m.id}',entity,kind='Derived from',evidence='Term occurrence; not a clinical causal claim')
 with store.factory() as s:
  for r in s.scalars(select(Relationship).where(Relationship.source_id.in_(ids),Relationship.target_id.in_(ids))):
   a,b=f'M{r.source_id}',f'M{r.target_id}'
   if g.has_edge(a,b):
    g.edges[a,b]['kind']+='; '+r.kind
    g.edges[a,b]['evidence']+=' | '+r.evidence
   else: g.add_edge(a,b,kind=r.kind,evidence=r.evidence)
 return g
