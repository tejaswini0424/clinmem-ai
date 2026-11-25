import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from backend.database.db_connection import connect
from backend.database.db_operations import Store
from backend.authentication.auth import register
@pytest.fixture
def store(tmp_path):
 factory=connect('sqlite:///'+str(tmp_path/'test.db'))
 return Store(factory,register(factory,'researcher','x','x'))
