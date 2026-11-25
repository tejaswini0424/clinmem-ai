import json,re
from difflib import SequenceMatcher
from datetime import datetime,timezone
def negated(text):
 # Safety disclaimers describe the prototype, not the polarity of an observation.
 text=re.sub(r'\bnot (?:verified )?clinical guidance\b','',text.lower())
 text=re.sub(r'\bno (?:dose or recommendation|treatment inference|causal or treatment conclusions)\b','',text)
 return bool(re.search(r'\b(no|not|never|ineffective|contraindicated|doesn.t)\b',text))

def potential_conflict(a,b):
 shared=set(json.loads(a.entities))&set(json.loads(b.entities))
 comparable=len(shared)>=2 or SequenceMatcher(None,a.content.lower(),b.content.lower()).ratio()>.7
 return bool(shared and comparable and negated(a.content)!=negated(b.content))
def run(store,ids=None,stale_days=1095):
 rows=store.memories(['Long-Term','Semantic'],False);findings=0
 for i,a in enumerate(rows):
  for b in rows[i+1:]:
   if ids is not None and a.id not in ids and b.id not in ids: continue
   if potential_conflict(a,b):
    for m in (a,b):
     if m.status!='Conflicting': store.update(m.id,status='Conflicting',reason='Heuristic potential polarity conflict; human review required')
    store.link(a.id,b.id,'Contradicts','Potential contradiction only; shared concepts and polarity differ. Human review required.');findings+=1
 for m in rows:
  if m.source_date and m.status=='Active':
   try: age=(datetime.now(timezone.utc).date()-datetime.fromisoformat(m.source_date).date()).days
   except ValueError: continue
   if age>stale_days:
    store.update(m.id,status='Pending Review',reason='Evidence age threshold reached; age alone does not establish obsolescence');findings+=1
 if findings: store.add(f'Evidence screening identified {findings} review findings.',memory_type='Episodic',source='System event')
 return {'records':len(rows),'findings':findings,'summary':f'{findings} heuristic review findings. No evidence overwritten.'}
