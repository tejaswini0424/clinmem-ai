import pytest
from backend.authentication.auth import register,login,logout
from backend.database.models import User
def test_auth(store):
 assert login(store.factory,'researcher','x')==store.user_id
 assert login(store.factory,'researcher','bad') is None
 with store.factory() as s: assert s.get(User,store.user_id).password_hash!='x'
 with pytest.raises(ValueError): register(store.factory,'researcher','y','y')
 with pytest.raises(ValueError): register(store.factory,'u','x','y')
 state={'uid':1};logout(state);assert not state
def test_long_unicode_password(store):
 password='🔬'*100;id=register(store.factory,' ','🔬'*100,password)
 assert login(store.factory,' ',password)==id
