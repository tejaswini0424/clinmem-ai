import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
BASE=Path(__file__).resolve().parents[1]
DATABASE_URL=os.getenv('CLINMEM_DB') or os.getenv('DATABASE_URL') or 'sqlite:///'+str(BASE/'data'/'clinmem.db')
if DATABASE_URL.startswith(('postgres://','postgresql://')):
 DATABASE_URL=DATABASE_URL.replace('postgres://','postgresql+psycopg://',1).replace('postgresql://','postgresql+psycopg://',1)
DISCLAIMER='Academic research prototype. Not a diagnosis or treatment recommendation. Synthetic records are not verified clinical guidance.'
STATUSES=['Active','Recently Updated','Outdated','Conflicting','Archived','Pending Review']
QUALITIES=['High','Moderate','Limited','Unknown']
