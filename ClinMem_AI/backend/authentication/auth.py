import bcrypt,hashlib
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from backend.database.models import User
def secret(password): return hashlib.sha256(password.encode()).hexdigest().encode()
def register(factory,username,password,confirm):
 if not username or not password: raise ValueError('Username and password must be non-empty.')
 if password!=confirm: raise ValueError('Passwords do not match.')
 with factory() as s:
  user=User(username=username,password_hash=bcrypt.hashpw(secret(password),bcrypt.gensalt()).decode());s.add(user)
  try: s.commit()
  except IntegrityError: s.rollback();raise ValueError('Username already exists.')
  return user.id
def login(factory,username,password):
 with factory() as s:
  user=s.scalar(select(User).where(User.username==username))
  return user.id if user and bcrypt.checkpw(secret(password),user.password_hash.encode()) else None
def logout(state): state.clear()
