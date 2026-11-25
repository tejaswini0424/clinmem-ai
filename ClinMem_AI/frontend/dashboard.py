import json,uuid,html
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import streamlit as st
from sqlalchemy import select
from config.settings import BASE,DISCLAIMER,STATUSES,QUALITIES
from backend.database.db_connection import connect
from backend.database.db_operations import Store
from backend.database.models import Document,AgentLog,Analysis,Version,Evidence
from backend.authentication.auth import register,login,logout
from backend.orchestration.orchestrator import Orchestrator
from backend.agents import memory_consolidation_agent as consolidation,evidence_updating_agent as updating,memory_evaluation_agent as evaluation
from backend.memory.memory_versioning import history
from backend.knowledge_graph.graph_manager import build
from backend.reports.pdf_generator import generate
from frontend.components import frame
from frontend.styles import apply

@st.cache_resource
def database(): return connect()

PAGES=['Overview Dashboard','Clinical Knowledge Assistant','Upload Knowledge Documents','Memory Explorer','Short-Term Memory','Long-Term Memory','Semantic Memory','Episodic Memory','Working Memory','Evidence Updating Center','Memory Version History','Knowledge Graph Explorer','Agent Activity Monitor','Memory Evaluation','Reports and Downloads','Settings']

def main():
 apply();factory=database()
 if 'uid' not in st.session_state:
  st.title('🧠 ClinMem AI');st.subheader('Adaptive Clinical Knowledge Memory')
  st.caption('Persistent knowledge · Traceable evidence · Human review')
  for tab,mode in zip(st.tabs(['Sign in','Create account']),['login','register']):
   with tab,st.form(mode):
    username=st.text_input('Username',key=mode+'user');password=st.text_input('Password',type='password',key=mode+'pass')
    confirm=st.text_input('Confirm password',type='password') if mode=='register' else ''
    if st.form_submit_button('Sign in' if mode=='login' else 'Create account',use_container_width=True):
     try:
      if mode=='register': register(factory,username,password,confirm);st.success('Account created. Sign in to continue.')
      else:
       uid=login(factory,username,password)
       if uid: st.session_state.update(uid=uid,username=username);st.rerun()
       else: st.error('Invalid credentials.')
     except ValueError as exc: st.error(str(exc))
  st.info(DISCLAIMER);return
 store=Store(factory,st.session_state.uid);orch=Orchestrator(store)
 with st.sidebar:
  st.title('🧠 ClinMem AI');st.caption('RESEARCH WORKSPACE')
  page=st.radio('Navigate',PAGES,label_visibility='collapsed')
  st.divider();st.caption('Signed in as '+st.session_state.username)
  if st.button('Logout',use_container_width=True): logout(st.session_state);st.rerun()
 st.title('ClinMem AI — Adaptive Clinical Knowledge Memory')
 st.caption(datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%d %B %Y · %H:%M:%S IST')+' · '+st.session_state.username)
 st.caption('Clock reflects the latest page interaction.');st.info(DISCLAIMER)
 rows=store.memories();df=frame(rows)
 with factory() as s:
  docs=list(s.scalars(select(Document).where(Document.user_id==store.user_id)))
  logs=list(s.scalars(select(AgentLog).where(AgentLog.user_id==store.user_id).order_by(AgentLog.id.desc())))
  analyses=list(s.scalars(select(Analysis).where(Analysis.user_id==store.user_id).order_by(Analysis.id.desc())))
 try:
  if page=='Overview Dashboard':
   st.subheader('Your knowledge, connected')
   metrics=[('Stored memories',len(rows)),('Active',sum(m.status=='Active' for m in rows)),('Recently updated',sum(m.status=='Recently Updated' for m in rows)),('Outdated',sum(m.status=='Outdated' for m in rows)),('Conflicting',sum(m.status=='Conflicting' for m in rows)),('Documents processed',sum(d.status=='Completed' for d in docs))]
   cols=st.columns(3)
   for i,(label,value) in enumerate(metrics): cols[i%3].metric(label,value)
   if rows:
    a,b=st.columns(2)
    a.plotly_chart(px.pie(df,names='Type',hole=.65,title='Memory composition'),use_container_width=True)
    b.plotly_chart(px.bar(df.groupby('Status').size().reset_index(name='Count'),x='Status',y='Count',title='Evidence lifecycle'),use_container_width=True)
    st.dataframe(df.tail(8),hide_index=True)
   else: st.info('Upload evidence or load the synthetic demonstration in Settings to begin.')
  elif page=='Clinical Knowledge Assistant':
   st.subheader('Ask your evidence library')
   query=st.text_area('Clinical knowledge question');k=st.slider('Top-k records',1,10,5)
   category=st.selectbox('Category',['All']+sorted({m.category for m in rows}));status=st.selectbox('Evidence status',['All']+STATUSES)
   if st.button('Retrieve and explain',type='primary'):
    with st.spinner('Retrieving and assembling source evidence…'):
     st.session_state.last_answer=orch.ask(query,k,category=None if category=='All' else category,status=None if status=='All' else status)
   if 'last_answer' in st.session_state:
    answer,results=st.session_state.last_answer;st.text(answer)
    for r in results:
     m=r['memory']
     with st.expander(f'[{m.id}] {m.source} · relevance {r["score"]:.3f}'):
      st.write(m.content);st.json({'memory_type':m.memory_type,'quality':m.quality,'status':m.status,'updated':m.updated,'source_page':m.page})
  elif page=='Upload Knowledge Documents':
   st.subheader('Add evidence with provenance')
   files=st.file_uploader('PDF, DOCX, TXT or CSV · up to 20 MB each',type=['pdf','docx','txt','csv'],accept_multiple_files=True)
   quality=st.selectbox('Reviewer-assigned evidence quality',QUALITIES,index=3)
   dated=st.checkbox('Document date is known');date=st.date_input('Source date') if dated else None
   if st.button('Process documents',disabled=not files):
    for file in files:
     with st.spinner('Processing '+file.name): result=orch.ingest(filename=file.name,data=file.getvalue(),quality=quality,source_date=date.isoformat() if date else None)
     (st.error if 'error' in result else st.success)(result['summary'])
   st.dataframe(pd.DataFrame([{'Document':d.filename,'Status':d.status,'Uploaded':d.uploaded} for d in docs]),hide_index=True)
  elif page in ['Memory Explorer','Short-Term Memory','Long-Term Memory','Semantic Memory','Episodic Memory','Working Memory']:
   st.subheader(page)
   subset=rows if page=='Memory Explorer' else [m for m in rows if m.memory_type==page.removesuffix(' Memory')]
   text=st.text_input('Search content or source');kind=st.selectbox('Memory type',['All']+sorted({m.memory_type for m in subset}));category=st.selectbox('Clinical category',['All']+sorted({m.category for m in subset}));status=st.selectbox('Status',['All']+STATUSES)
   subset=[m for m in subset if text.lower() in (m.content+' '+(m.source or '')).lower() and (kind=='All' or m.memory_type==kind) and (category=='All' or m.category==category) and (status=='All' or m.status==status)]
   st.dataframe(frame(subset),hide_index=True,use_container_width=True)
   if page=='Working Memory': st.caption('Working records exist only during an active retrieval and are cleared in a finally block when the task ends.')
   if subset:
    id=st.selectbox('Inspect memory',[m.id for m in subset]);m=next(m for m in subset if m.id==id);st.write(m.content)
    with factory() as s:
     evidence=list(s.scalars(select(Evidence).where(Evidence.memory_id==id)))
    st.json([{'source':e.source,'source_date':e.source_date,'original_excerpt':e.description,'quality':e.quality,'verification':e.verification} for e in evidence])
    action=st.selectbox('Lifecycle action',['Archived','Active','Pending Review','Outdated','Conflicting'])
    if st.button('Apply lifecycle action'): store.update(id,status=action);st.rerun()
    st.dataframe(pd.DataFrame([{'Version':v.number,'Previous':v.previous,'Content':v.content,'Reason':v.reason,'Date':v.date} for v in history(store,id)]),hide_index=True)
  elif page=='Evidence Updating Center':
   st.subheader('Review changes and preserve competing evidence')
   if st.button('Screen evidence for possible conflicts and age'): st.json(orch.execute('Evidence Updating',updating.run))
   st.dataframe(frame([m for m in rows if m.status in ['Conflicting','Pending Review','Outdated']]),hide_index=True)
   candidates=[m for m in rows if m.memory_type in ['Long-Term','Semantic']]
   if candidates:
    id=st.selectbox('Record to revise',[m.id for m in candidates]);m=next(m for m in candidates if m.id==id)
    with st.form('revision'):
     content=st.text_area('Reviewed content',m.content);reason=st.text_input('Review reason');status=st.selectbox('Reviewed status',STATUSES)
     if st.form_submit_button('Save new version'):
      if not reason.strip(): st.error('Record a review reason.')
      else: store.update(id,content,status,reason);st.success('Version saved; original evidence preserved.')
    other=st.selectbox('New evidence that explicitly supersedes this record',[None]+[x.id for x in candidates if x.id!=id])
    rationale=st.text_input('Supersession source reference and reviewer rationale')
    if st.button('Confirm reviewed supersession',disabled=other is None or not rationale.strip()):
     store.link(other,id,'Supersedes',rationale);store.update(id,status='Outdated',reason=rationale);store.update(other,status='Recently Updated',reason=rationale);st.success('Reviewed supersession recorded.')
  elif page=='Memory Version History':
   if rows:
    id=st.selectbox('Memory ID',[m.id for m in rows]);st.dataframe(pd.DataFrame([{'Version':v.number,'Previous content':v.previous,'New content':v.content,'Reason':v.reason,'Date':v.date} for v in history(store,id)]),hide_index=True)
   else: st.info('No memory versions yet.')
  elif page=='Knowledge Graph Explorer':
   if st.button('Consolidate shared concepts'): st.json(orch.execute('Memory Consolidation',consolidation.run))
   g=build(store)
   if g:
    pos=nx.spring_layout(g,seed=42);ex=[];ey=[]
    for a,b in g.edges: ex.extend([pos[a][0],pos[b][0],None]);ey.extend([pos[a][1],pos[b][1],None])
    fig=go.Figure([go.Scatter(x=ex,y=ey,mode='lines',line=dict(color='#285e72'),hoverinfo='skip'),go.Scatter(x=[pos[n][0] for n in g],y=[pos[n][1] for n in g],mode='markers+text',text=[g.nodes[n]['label'] for n in g],textposition='top center',marker=dict(size=14,color='#29d3bf'))]);fig.update_layout(showlegend=False,height=550)
    st.plotly_chart(fig,use_container_width=True);node=st.selectbox('Inspect node',list(g));st.json(dict(g.nodes[node]));st.json([{'connected_entity':n,**g.edges[node,n]} for n in g.neighbors(node)])
   else: st.info('No concepts stored yet.')
  elif page=='Agent Activity Monitor':
   st.caption('Encoding → Updating → Consolidation | Retrieval → Reasoning → Evaluation')
   for name in ['Memory Encoding','Memory Retrieval','Memory Consolidation','Evidence Updating','Clinical Reasoning','Memory Evaluation']:
    latest=next((l for l in logs if l.agent==name),None)
    with st.expander(name,expanded=True):
     if latest: st.write(f'{latest.status} · {latest.duration:.3f}s · {latest.records} records · {latest.findings} findings');st.write(latest.summary)
     else: st.write('Pending — no execution recorded.')
   st.dataframe(pd.DataFrame([{'Agent':l.agent,'Status':l.status,'Duration':l.duration,'Input':l.input_summary,'Output':l.summary,'Date':l.date} for l in logs]),hide_index=True)
  elif page=='Memory Evaluation':
   st.warning('Synthetic demonstration benchmark. Results are not validated clinical performance.')
   k=st.slider('Evaluation top-k',1,10,3)
   if st.button('Run labeled synthetic benchmark'):
    specs=json.loads((BASE/'data/evaluation_queries.json').read_text());queries=[]
    for q in specs:
     expected=[m.id for m in rows if m.source in q['sources']]
     if expected: queries.append({'query':q['query'],'expected_ids':expected})
    result=orch.execute('Memory Evaluation',evaluation.run,queries=queries,k=k);st.json(result)
    if result.get('metrics'):
     metrics=pd.DataFrame(result['metrics']);st.metric('Mean precision',f'{metrics.precision.mean():.3f}');st.metric('Mean recall',f'{metrics.recall.mean():.3f}');st.dataframe(metrics)
    else: st.info('Load synthetic demonstration records in Settings first.')
   st.metric('Agent execution success rate',f'{sum(l.status=="Completed" for l in logs)/len(logs):.1%}' if logs else 'No executions')
   with factory() as s:
    ids=[m.id for m in rows];updates=list(s.scalars(select(Version).where(Version.memory_id.in_(ids),Version.number>1)))
   st.metric('Versioned update events',len(updates))
  elif page=='Reports and Downloads':
   st.download_button('Download memory CSV',df.to_csv(index=False).encode('utf-8'),file_name='clinmem_memories.csv',mime='text/csv')
   st.download_button('Download memory JSON',df.to_json(orient='records',indent=2),file_name='clinmem_memories.json',mime='application/json')
   selected=st.selectbox('Analysis to include',[None]+[a.id for a in analyses]);analysis=next((a for a in analyses if a.id==selected),None)
   sections=[('Query',analysis.query if analysis else 'No analysis selected'),('Answer',analysis.answer if analysis else 'No generated answer'),('Retrieved memory IDs',analysis.memory_ids if analysis else '[]')]
   for m in rows:
    sections.append((f'Memory {m.id} · {m.memory_type}',f'{m.content}\nSource: {m.source}; page: {m.page}; date: {m.source_date}; quality: {m.quality}; status: {m.status}; updated: {m.updated}'))
    sections.append((f'Versions for memory {m.id}','\n'.join(f'v{v.number}: {v.reason}; {v.date}; previous: {v.previous}; new: {v.content}' for v in history(store,m.id))))
   sections.append(('Agent activity','\n'.join(f'{l.agent}: {l.status}; {l.duration:.3f}s; {l.summary}' for l in logs[:30])))
   st.download_button('Download PDF research report',generate('ClinMem AI Research Report',sections),file_name='clinmem_report.pdf',mime='application/pdf')
  elif page=='Settings':
   st.subheader('Local research configuration');st.write('Offline TF-IDF character similarity + keyword, evidence quality and recency ranking. No paid API. No network model download.')
   st.caption('Evidence quality is assigned by the uploader and is not independently validated. Each account owns its records. Do not upload identifiable patient data to this research prototype.')
   if st.button('Load clearly labeled synthetic demonstration'):
    for record in json.loads((BASE/'data/sample_evidence.json').read_text()): store.add(**record)
    orch.execute('Evidence Updating',updating.run);orch.execute('Memory Consolidation',consolidation.run);st.success('Synthetic evidence loaded. Repeated loading skips identical source records.')
   st.caption('Optional cached Sentence Transformers encoder: install sentence-transformers separately and set CLINMEM_EMBEDDINGS=sentence-transformers. Unavailable cached models fall back locally.')
 except Exception as exc: st.error(f'Operation could not complete: {exc}. Other pages remain available.')
