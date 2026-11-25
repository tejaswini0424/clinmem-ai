from pathlib import Path
from streamlit.testing.v1 import AppTest
from frontend.dashboard import PAGES

def test_login_and_authenticated_pages(store,monkeypatch):
 import json
 base=Path(__file__).resolve().parents[1]
 for record in json.loads((base/'data/sample_evidence.json').read_text()): store.add(**record)
 import frontend.dashboard as dashboard
 monkeypatch.setattr(dashboard,'database',lambda:store.factory)
 app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=30)
 assert not app.exception
 app.text_input(key='loginuser').set_value('researcher')
 app.text_input(key='loginpass').set_value('x')
 app.button[0].click().run(timeout=30)
 assert app.session_state['uid']==store.user_id
 for page in PAGES:
  app.sidebar.radio[0].set_value(page).run(timeout=30)
  assert not app.exception, page
  assert not app.error, page
 app.sidebar.radio[0].set_value('Clinical Knowledge Assistant').run()
 app.text_area[0].set_value('diabetes glucose intervention alpha')
 app.button[0].click().run(timeout=30)
 assert not app.error and not app.exception
 assert 'SYNTHETIC' in app.session_state['last_answer'][0]
 app.sidebar.button[0].click().run(timeout=30)
 assert len(app.text_input)==5
