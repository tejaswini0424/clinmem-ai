"""Vercel-compatible HTTP interface; reuses the local research backend."""
import csv
import hashlib
import io
import json
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import Column, ForeignKey, Integer, String, delete, select, text
from sqlalchemy.exc import SQLAlchemyError

from backend.authentication.auth import login, register
from backend.database.db_connection import connect
from backend.database.db_operations import Store
from backend.database.models import AgentLog, Analysis, Base, Document, Evidence, User, Version
from backend.memory.memory_versioning import history
from backend.orchestration.orchestrator import Orchestrator
from backend.agents import evidence_updating_agent, memory_consolidation_agent, memory_evaluation_agent
from config.settings import BASE, DATABASE_URL, DISCLAIMER, QUALITIES, STATUSES

class WebSession(Base):
    __tablename__ = 'web_sessions'
    token_hash = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    expires = Column(String, nullable=False)

app = FastAPI(title='ClinMem AI', docs_url=None, redoc_url=None)
COOKIE = 'clinmem_session'

@lru_cache
def factory():
    if os.getenv('VERCEL') and DATABASE_URL.startswith('sqlite:'):
        raise HTTPException(503, 'A persistent cloud database must be configured before using this deployment.')
    return connect()

def fields(row):
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}

@app.middleware('http')
async def browser_security(request: Request, call_next):
    origin = request.headers.get('origin')
    if request.method not in ('GET', 'HEAD', 'OPTIONS') and origin and urlparse(origin).netloc != request.headers.get('host'):
        return JSONResponse({'detail': 'Cross-origin requests are not permitted.'}, status_code=403)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response

@app.exception_handler(ValueError)
async def invalid(request, exc):
    return JSONResponse({'detail': str(exc)}, status_code=400)

@app.exception_handler(SQLAlchemyError)
async def database_error(request, exc):
    logging.exception('Database operation failed')
    return JSONResponse({'detail': 'Storage is temporarily unavailable. Please retry.'}, status_code=503)

def current_user(request: Request):
    token = request.cookies.get(COOKIE, '')
    if not token:
        raise HTTPException(401, 'Please sign in.')
    with factory()() as db:
        session = db.get(WebSession, hashlib.sha256(token.encode()).hexdigest())
        if not session or datetime.fromisoformat(session.expires) <= datetime.now(timezone.utc):
            raise HTTPException(401, 'Session expired. Please sign in.')
        user = db.get(User, session.user_id)
        if not user:
            raise HTTPException(401, 'Account unavailable.')
        return user

def user_store(user=Depends(current_user)):
    return Store(factory(), user.id)

class Credentials(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    confirm: str = ''

def identity(user):
    guest = user.username.startswith('guest:')
    return {'username': 'Visitor workspace' if guest else user.username, 'guest': guest}

def issue_session(uid, response, request):
    token = secrets.token_urlsafe(48)
    expiry = datetime.now(timezone.utc) + timedelta(hours=12)
    with factory()() as db:
        db.execute(delete(WebSession).where(WebSession.expires < datetime.now(timezone.utc).isoformat()))
        db.add(WebSession(token_hash=hashlib.sha256(token.encode()).hexdigest(), user_id=uid, expires=expiry.isoformat()))
        db.commit()
    response.set_cookie(COOKIE, token, max_age=43200, httponly=True, secure=bool(os.getenv('VERCEL')) or request.url.scheme=='https', samesite='strict', path='/')

@app.post('/api/auth/guest')
def public_workspace(response: Response, request: Request):
    """Open an isolated visitor workspace without exposing another user's data."""
    try:
        return identity(current_user(request))
    except HTTPException as exc:
        if exc.status_code != 401:
            raise
    username = 'guest:' + secrets.token_hex(24)
    password = secrets.token_urlsafe(48)
    uid = register(factory(), username, password, password)
    from backend.memory.demo_library import seed_visitor
    seed_visitor(factory(), uid)
    issue_session(uid, response, request)
    return {'username': 'Visitor workspace', 'guest': True}

@app.post('/api/auth/register')
def create_account(body: Credentials):
    register(factory(), body.username, body.password, body.confirm)
    return {'message': 'Account created. You can sign in.'}

@app.post('/api/auth/login')
def sign_in(body: Credentials, response: Response, request: Request):
    uid = login(factory(), body.username, body.password)
    if not uid:
        raise HTTPException(401, 'Invalid username or password.')
    issue_session(uid, response, request)
    with factory()() as db:
        return identity(db.get(User, uid))

@app.post('/api/auth/logout')
def sign_out(request: Request, response: Response):
    token = request.cookies.get(COOKIE)
    if token:
        with factory()() as db:
            db.execute(delete(WebSession).where(WebSession.token_hash==hashlib.sha256(token.encode()).hexdigest()))
            db.commit()
    response.delete_cookie(COOKIE, path='/')
    return {'message': 'Signed out.'}

@app.get('/api/auth/me')
def me(user=Depends(current_user)):
    return identity(user)

@app.get('/api/health')
def health():
    with factory()() as db:
        db.execute(text('SELECT 1'))
    return {'status': 'ok', 'storage': 'postgresql' if DATABASE_URL.startswith('postgresql') else 'local-sqlite'}

@app.get('/api/workspace')
def workspace(store=Depends(user_store)):
    memories = store.memories()
    ids = [m.id for m in memories]
    with store.factory() as db:
        documents = list(db.scalars(select(Document).where(Document.user_id==store.user_id)))
        logs = list(db.scalars(select(AgentLog).where(AgentLog.user_id==store.user_id).order_by(AgentLog.id.desc()).limit(200)))
        analyses = list(db.scalars(select(Analysis).where(Analysis.user_id==store.user_id).order_by(Analysis.id.desc()).limit(50)))
        versions = list(db.scalars(select(Version).where(Version.memory_id.in_(ids)).order_by(Version.id.desc())))
        evidence = list(db.scalars(select(Evidence).where(Evidence.memory_id.in_(ids))))
    return {'memories': [fields(m) for m in memories], 'documents': [fields(d) for d in documents], 'logs': [fields(l) for l in logs], 'analyses': [fields(a) for a in analyses], 'versions': [fields(v) for v in versions], 'evidence': [fields(e) for e in evidence], 'statuses': STATUSES, 'qualities': QUALITIES, 'disclaimer': DISCLAIMER}

class Question(BaseModel):
    query: str = Field(min_length=1)
    k: int = Field(default=5, ge=1, le=10)
    category: str | None = None
    status: str | None = None

@app.post('/api/assistant')
def assistant(body: Question, store=Depends(user_store)):
    answer, results = Orchestrator(store).ask(body.query, body.k, category=body.category, status=body.status)
    return {'answer': answer, 'results': [{'memory': fields(r['memory']), 'score': r['score'], 'match': r.get('match','Hybrid text relevance')} for r in results]}

@app.post('/api/upload')
def upload(file: UploadFile = File(...), quality: str = Form('Unknown'), source_date: str = Form(''), store=Depends(user_store)):
    if quality not in QUALITIES:
        raise ValueError('Invalid evidence quality.')
    if source_date:
        datetime.fromisoformat(source_date)
    data = file.file.read(4*1024*1024+1)
    if len(data)>4*1024*1024:
        raise ValueError('Cloud uploads are limited to 4 MB per file.')
    result = Orchestrator(store).ingest(filename=Path(file.filename or 'upload.txt').name, data=data, quality=quality, source_date=source_date or None)
    if result.get('error'):
        raise ValueError(result['summary'])
    return result

@app.post('/api/sample')
def sample(store=Depends(user_store)):
    for record in json.loads((BASE/'data/sample_evidence.json').read_text()):
        store.add(**record)
    orch=Orchestrator(store)
    update=orch.execute('Evidence Updating', evidence_updating_agent.run)
    links=orch.execute('Memory Consolidation', memory_consolidation_agent.run)
    return {'message': 'Synthetic demonstration evidence loaded.', 'update': update, 'links': links}

@app.post('/api/screen')
def screen(store=Depends(user_store)):
    return Orchestrator(store).execute('Evidence Updating', evidence_updating_agent.run)

@app.post('/api/consolidate')
def consolidate(store=Depends(user_store)):
    return Orchestrator(store).execute('Memory Consolidation', memory_consolidation_agent.run)

class Edit(BaseModel):
    content: str | None = None
    status: str | None = None
    reason: str = Field(min_length=1)

@app.patch('/api/memories/{id}')
def edit(id: int, body: Edit, store=Depends(user_store)):
    store.update(id, content=body.content, status=body.status, reason=body.reason)
    return {'message': 'New version saved. Original evidence retained.'}

class Supersede(BaseModel):
    older: int
    newer: int
    reason: str = Field(min_length=1)

@app.post('/api/supersede')
def supersede(body: Supersede, store=Depends(user_store)):
    if body.older==body.newer:
        raise ValueError('Select two different evidence records.')
    with store.factory() as db:
        store.get(db, body.older)
        store.get(db, body.newer)
    store.link(body.newer, body.older, 'Supersedes', body.reason)
    store.update(body.older, status='Outdated', reason=body.reason)
    store.update(body.newer, status='Recently Updated', reason=body.reason)
    return {'message':'Reviewed supersession recorded.'}

@app.get('/api/graph')
def graph(store=Depends(user_store)):
    from backend.knowledge_graph.graph_manager import build
    import networkx as nx
    g=build(store)
    positions=nx.spring_layout(g, seed=42)
    return {'nodes':[{'id':node, **g.nodes[node], 'x':float(positions[node][0]), 'y':float(positions[node][1])} for node in g], 'edges':[{'source':a,'target':b,**data} for a,b,data in g.edges(data=True)]}

@app.post('/api/evaluate')
def evaluate(k: int=3, store=Depends(user_store)):
    if k<1 or k>10:
        raise ValueError('Top-k must be between 1 and 10.')
    rows=store.memories(['Long-Term','Semantic'])
    queries=[]
    for item in json.loads((BASE/'data/evaluation_queries.json').read_text()):
        expected=[m.id for m in rows if m.source in item['sources']]
        if expected:
            queries.append({'query':item['query'], 'expected_ids':expected})
    return Orchestrator(store).execute('Memory Evaluation',memory_evaluation_agent.run,queries=queries,k=k)

@app.get('/api/export/{format}')
def export(format: str, analysis_id: int | None=None, store=Depends(user_store)):
    rows=store.memories()
    records=[fields(m) for m in rows]
    headers={'Content-Disposition': f'attachment; filename="clinmem_memories.{format}"'}
    if format=='json':
        return Response(json.dumps(records,ensure_ascii=False,indent=2),media_type='application/json',headers=headers)
    if format=='csv':
        output=io.StringIO()
        writer=csv.DictWriter(output,fieldnames=list(records[0]) if records else ['id','content','source','status'])
        writer.writeheader();writer.writerows(records)
        return Response(output.getvalue(),media_type='text/csv',headers=headers)
    if format!='pdf':
        raise HTTPException(404,'Export format unavailable.')
    from backend.reports.pdf_generator import generate
    sections=[]
    with store.factory() as db:
        analysis=db.scalar(select(Analysis).where(Analysis.id==analysis_id,Analysis.user_id==store.user_id)) if analysis_id else None
        logs=list(db.scalars(select(AgentLog).where(AgentLog.user_id==store.user_id).order_by(AgentLog.id.desc()).limit(30)))
    if analysis:
        sections.extend([('Question',analysis.query),('Answer',analysis.answer),('Retrieved IDs',analysis.memory_ids)])
    for memory in rows:
        sections.append((f'Memory {memory.id} · {memory.memory_type}', f'{memory.content}\nSource: {memory.source}; page: {memory.page}; quality: {memory.quality}; status: {memory.status}; updated: {memory.updated}'))
        sections.append((f'History {memory.id}', '\n'.join(f'v{v.number}: {v.reason}; previous: {v.previous}; new: {v.content}' for v in history(store,memory.id))))
    sections.append(('Agent activity','\n'.join(f'{l.agent}: {l.status}; {l.duration:.3f}s; {l.summary}' for l in logs)))
    return Response(generate('ClinMem AI Research Report',sections),media_type='application/pdf',headers=headers)

@app.get('/')
def index():
    return FileResponse(BASE/'web/index.html')

app.mount('/assets', StaticFiles(directory=BASE/'web'), name='assets')
