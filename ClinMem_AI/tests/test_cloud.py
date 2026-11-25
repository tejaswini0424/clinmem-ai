import pytest
from fastapi.testclient import TestClient
import server

@pytest.fixture
def client(store,monkeypatch):
    monkeypatch.setattr(server,'factory',lambda:store.factory)
    return TestClient(server.app,base_url='https://testserver')

def authenticate(client,name='cloud-researcher'):
    body={'username':name,'password':'p','confirm':'p'}
    assert client.post('/api/auth/register',json=body).status_code==200
    response=client.post('/api/auth/login',json=body)
    assert response.status_code==200
    assert 'HttpOnly' in response.headers['set-cookie']

def test_cloud_auth_and_isolation(client,store):
    assert client.get('/').status_code==200
    assert client.get('/api/workspace').status_code==401
    store.add('Other account private evidence')
    authenticate(client)
    assert client.get('/api/workspace').json()['memories']==[]
    assert client.patch('/api/memories/1',json={'status':'Archived','reason':'unauthorized'}).status_code==400
    token=client.cookies.get(server.COOKIE)
    assert client.post('/api/auth/logout').status_code==200
    assert client.get('/api/workspace',headers={'Cookie':f'{server.COOKIE}={token}'}).status_code==401

def test_cloud_end_to_end(client):
    authenticate(client)
    result=client.post('/api/sample')
    assert result.status_code==200
    assert result.json()['update']['findings']==1
    answer=client.post('/api/assistant',json={'query':'diabetes glucose intervention alpha','k':3})
    assert answer.status_code==200 and 'Conflicting' in answer.json()['answer']
    benchmark=client.post('/api/evaluate?k=3').json()
    assert len(benchmark['metrics'])==4
    assert all(m['recall']==1 for m in benchmark['metrics'])
    graph=client.get('/api/graph').json()
    assert any('Contradicts' in e['kind'] for e in graph['edges'])
    workspace=client.get('/api/workspace').json()
    assert workspace['analyses'] and workspace['versions'] and workspace['logs']
    assert not any(m['memory_type']=='Working' for m in workspace['memories'])
    for format in ('pdf','csv','json'):
        response=client.get('/api/export/'+format)
        assert response.status_code==200 and response.content
    upload=client.post('/api/upload',files={'file':('evidence.txt',b'SYNTHETIC diabetes glucose source')})
    assert upload.status_code==200
    assert client.post('/api/upload',files={'file':('bad.exe',b'bad')}).status_code==400

def test_cloud_origin_validation(client):
    response=client.post('/api/auth/login',json={'username':'x','password':'x'},headers={'Origin':'https://untrusted.example'})
    assert response.status_code==403

def test_cloud_version_and_supersession(client):
    authenticate(client)
    client.post('/api/sample')
    rows=client.get('/api/workspace').json()['memories']
    ids=[m['id'] for m in rows if m['memory_type']=='Long-Term']
    assert client.patch(f'/api/memories/{ids[0]}',json={'content':'SYNTHETIC reviewed diabetes evidence','status':'Pending Review','reason':'Human source review'}).status_code==200
    response=client.post('/api/supersede',json={'older':ids[0],'newer':ids[1],'reason':'Explicit synthetic source supersession'})
    assert response.status_code==200
    rows=client.get('/api/workspace').json()['memories']
    assert next(m for m in rows if m['id']==ids[0])['status']=='Outdated'

def test_public_dashboard_isolated_guest_workspace(client,store):
    private_id=store.add('PRIVATE clinical evidence owned by an existing account')
    response=client.post('/api/auth/guest')
    assert response.status_code==200 and response.json()['guest'] is True
    assert 'HttpOnly' in response.headers['set-cookie']
    first=client.get('/api/workspace').json()
    evidence=[m for m in first['memories'] if m['memory_type'] in ['Long-Term','Semantic']]
    assert len(evidence)==5
    assert all('SYNTHETIC DEMO' in m['content'] for m in evidence)
    assert private_id not in [m['id'] for m in first['memories']]
    assert sum(m['status']=='Conflicting' for m in evidence)==2
    assert all(any(v['memory_id']==m['id'] and v['number']==1 for v in first['versions']) for m in evidence)
    assert all(any(v['memory_id']==m['id'] and v['number']==2 for v in first['versions']) for m in evidence if m['status']=='Conflicting')
    assert len(first['logs'])==2
    assert any('Contradicts' in edge['kind'] and 'Related to' in edge['kind'] for edge in client.get('/api/graph').json()['edges'])
    assert client.post('/api/auth/guest').json()['guest'] is True
    assert [m['id'] for m in client.get('/api/workspace').json()['memories']]==[m['id'] for m in first['memories']]
    other=TestClient(server.app,base_url='https://testserver')
    assert other.post('/api/auth/guest').status_code==200
    second=other.get('/api/workspace').json()
    assert not set(m['id'] for m in first['memories']) & set(m['id'] for m in second['memories'])
    assert other.patch('/api/memories/'+str(evidence[0]['id']),json={'status':'Archived','reason':'Forbidden cross-visitor edit'}).status_code==400

def test_public_dashboard_preserves_signed_in_account(client):
    authenticate(client)
    response=client.post('/api/auth/guest')
    assert response.json()=={'username':'cloud-researcher','guest':False}
    assert client.get('/api/workspace').json()['memories']==[]
