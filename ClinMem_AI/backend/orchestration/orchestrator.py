import time,json,uuid
from sqlalchemy.exc import OperationalError
from backend.database.models import AgentLog,Analysis
from backend.agents import memory_encoding_agent as encoding,memory_retrieval_agent as retrieval,memory_consolidation_agent as consolidation,evidence_updating_agent as updating,clinical_reasoning_agent as reasoning,memory_evaluation_agent as evaluation
from backend.memory.memory_manager import clear_working,expire_context
class Orchestrator:
 def __init__(self,store): self.store=store
 def execute(self,name,fn,**kwargs):
  start=time.perf_counter()
  with self.store.factory() as s:
   log=AgentLog(user_id=self.store.user_id,agent=name,status='Running',duration=0,input_summary=str({k:(f'{len(v)} bytes' if isinstance(v,bytes) else str(v)[:200]) for k,v in kwargs.items()}));s.add(log);s.commit();id=log.id
  try:
   for attempt in range(2):
    try: result=fn(self.store,**kwargs);break
    except OperationalError:
     if attempt: raise
   status='Completed'
  except Exception as exc: result={'records':0,'findings':0,'summary':str(exc),'error':str(exc)};status='Failed'
  with self.store.factory() as s:
   log=s.get(AgentLog,id);log.status=status;log.duration=time.perf_counter()-start;log.records=result.get('records',0);log.findings=result.get('findings',0);log.summary=result.get('summary','');s.commit()
  return result
 def ingest(self,**kwargs):
  result=self.execute('Memory Encoding',encoding.run,**kwargs)
  if 'error' not in result:
   self.execute('Evidence Updating',updating.run,ids=result['ids']);self.execute('Memory Consolidation',consolidation.run)
  return result
 def ask(self,query,k=5,**filters):
  if not query.strip(): raise ValueError('Enter a question.')
  expire_context(self.store);session=uuid.uuid4().hex
  try:
   ret=self.execute('Memory Retrieval',retrieval.run,query=query,k=k,**filters);results=ret.get('results',[])
   for r in results: self.store.add(r['memory'].content,memory_type='Working',session_id=session,source=f"Memory {r['memory'].id}")
   result=self.execute('Clinical Reasoning',reasoning.run,query=query,results=results)
   answer=result.get('answer','Explanation unavailable because the reasoning agent failed.')
   self.execute('Memory Evaluation',evaluation.run)
   self.store.add(query,memory_type='Short-Term',session_id=session,source='User query')
   self.store.add('Retrieved memory IDs: '+str([r['memory'].id for r in results]),memory_type='Short-Term',session_id=session,source='Retrieval context')
   with self.store.factory() as s: s.add(Analysis(user_id=self.store.user_id,query=query,answer=answer,memory_ids=json.dumps([r['memory'].id for r in results])));s.commit()
   return answer,results
  finally: clear_working(self.store,session)
