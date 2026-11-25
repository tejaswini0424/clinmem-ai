"""Bulk-initialize a new visitor's synthetic library in one transaction."""
import json
import time
from backend.database.models import Memory, Evidence, Version, Relationship, AgentLog, now
from backend.database.db_operations import digest
from backend.ingestion.text_processor import clean, entities, category
from backend.agents.evidence_updating_agent import potential_conflict
from config.settings import BASE

def seed_visitor(factory,user_id):
    start=time.perf_counter()
    with factory() as db:
        rows=[]
        for record in json.loads((BASE/'data/sample_evidence.json').read_text()):
            content=clean(record['content'])
            memory=Memory(user_id=user_id,content=content,digest=digest(content),entities=json.dumps(entities(content)),category=category(content),source=record['source'],quality=record['quality'],memory_type=record['memory_type'])
            rows.append(memory)
        db.add_all(rows)
        db.flush()
        conflicts=set()
        links=0
        findings=0
        for i,a in enumerate(rows):
            for b in rows[i+1:]:
                shared=set(json.loads(a.entities))&set(json.loads(b.entities))
                if shared:
                    db.add(Relationship(source_id=a.id,target_id=b.id,kind='Related to',evidence='Inferred shared terms: '+', '.join(sorted(shared))))
                    links+=1
                if potential_conflict(a,b):
                    db.add(Relationship(source_id=a.id,target_id=b.id,kind='Contradicts',evidence='Potential contradiction only; shared concepts and polarity differ. Human review required.'))
                    conflicts.update((a.id,b.id))
                    findings+=1
        screening_duration=time.perf_counter()-start
        if findings:
            content=f'Evidence screening identified {findings} review findings.'
            event=Memory(user_id=user_id,content=content,digest=digest(content),entities='[]',category='General',memory_type='Episodic',source='System event',quality='Unknown')
            db.add(event);db.flush();all_rows=rows+[event]
        else:
            all_rows=rows
        for memory in all_rows:
            db.add(Evidence(memory_id=memory.id,source=memory.source,description=memory.content,quality=memory.quality))
            db.add(Version(memory_id=memory.id,number=1,previous='',content=memory.content,reason='Created'))
            if memory.id in conflicts:
                memory.status='Conflicting';memory.version=2;memory.updated=now()
                db.add(Version(memory_id=memory.id,number=2,previous=memory.content,content=memory.content,reason='Heuristic potential polarity conflict; human review required; status Active → Conflicting'))
        db.add(AgentLog(user_id=user_id,agent='Evidence Updating',status='Completed',duration=screening_duration,records=len(rows),findings=findings,input_summary='New visitor synthetic library',summary=f'{findings} heuristic review findings. No evidence overwritten.'))
        db.add(AgentLog(user_id=user_id,agent='Memory Consolidation',status='Completed',duration=time.perf_counter()-start,records=len(rows),findings=links,input_summary='New visitor synthetic library',summary=f'{links} shared-concept pairs linked; original evidence preserved.'))
        db.commit()
