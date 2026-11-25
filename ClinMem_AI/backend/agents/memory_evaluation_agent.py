from collections import Counter
from backend.evaluation.metrics import precision_recall
from backend.retrieval.hybrid_retriever import search
def run(store,queries=None,k=3):
 rows=store.memories(['Long-Term','Semantic']);counts=Counter(m.digest for m in rows)
 metrics=[]
 for q in queries or []:
  expected=q['expected_ids'];actual=[r['memory'].id for r in search(store,q['query'],k)]
  metrics.append({'query':q['query'],'actual_ids':actual,'expected_ids':expected,**precision_recall(actual,expected,k)})
 return {'records':len(rows),'findings':sum(v-1 for v in counts.values()),'summary':'Synthetic benchmark only; not clinical validation.','metrics':metrics,'duplicates':sum(v-1 for v in counts.values()),'outdated':sum(m.status=='Outdated' for m in rows),'conflicting':sum(m.status=='Conflicting' for m in rows)}
