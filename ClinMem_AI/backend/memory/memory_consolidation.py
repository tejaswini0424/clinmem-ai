import json
def consolidate(store):
 rows=store.memories(['Long-Term','Semantic'],False);count=0
 for i,a in enumerate(rows):
  for b in rows[i+1:]:
   common=set(json.loads(a.entities))&set(json.loads(b.entities))
   if common:
    store.link(a.id,b.id,'Related to','Inferred shared terms: '+', '.join(sorted(common)));count+=1
 return {'records':len(rows),'findings':count,'summary':f'{count} shared-concept pairs linked; original evidence preserved.'}
