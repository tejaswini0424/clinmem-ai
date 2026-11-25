from backend.retrieval.hybrid_retriever import search
def run(store,query,k=5,**filters):
 results=search(store,query,k,**filters)
 recent=[m for m in store.memories(['Short-Term'],False) if query.lower() in m.content.lower()][-5:]
 return {'records':len(results),'findings':len(recent),'summary':f'Retrieved {len(results)} evidence records and {len(recent)} recent context records.','results':results,'recent':recent}
