import re
from datetime import datetime,timezone
from backend.retrieval.embeddings import encode
from backend.retrieval.vector_store import similarities
QUALITY={'High':1,'Moderate':.7,'Limited':.3,'Unknown':0}
def search(store,query,k=5,category=None,status=None):
 if not query.strip(): return []
 rows=[m for m in store.memories(['Long-Term','Semantic'],False) if (not category or m.category==category) and (not status or m.status==status)]
 if not rows: return []
 intent=query.lower()
 # Library questions are answered from stored metadata, without inventing evidence.
 requested_status=next((value for phrase,value in [('outdated','Outdated'),('conflict','Conflicting'),('pending review','Pending Review'),('archived','Archived')] if phrase in intent),None)
 if requested_status:
  return [{'memory':m,'score':1.,'similarity':0.,'match':'Status metadata'} for m in rows if m.status==requested_status][:k]
 if any(phrase in intent for phrase in ['added recently','new evidence','latest knowledge','recent updates','what changed']):
  return [{'memory':m,'score':1.,'similarity':0.,'match':'Most recently updated metadata'} for m in sorted(rows,key=lambda m:m.updated,reverse=True)[:k]]
 if any(phrase in intent for phrase in ['what clinical knowledge','what knowledge is stored','list stored','show all memories']):
  return [{'memory':m,'score':1.,'similarity':0.,'match':'Library inventory'} for m in rows[:k]]
 scores=similarities(encode([m.content for m in rows]+[query]));tokens=set(re.findall(r'\w+',query.lower()));results=[]
 for m,similarity in zip(rows,scores):
  words=set(re.findall(r'\w+',m.content.lower()));keyword=len(tokens&words)/max(1,len(tokens))
  if similarity<.12 and keyword==0: continue
  age=max(0,(datetime.now(timezone.utc)-datetime.fromisoformat(m.updated)).days)
  score=.7*float(similarity)+.2*keyword+.06*QUALITY.get(m.quality,0)+.04/(1+age/365)
  results.append({'memory':m,'score':score,'similarity':float(similarity)})
 return sorted(results,key=lambda r:r['score'],reverse=True)[:k]
