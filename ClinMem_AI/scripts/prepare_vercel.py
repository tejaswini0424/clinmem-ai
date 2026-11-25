"""Create a deployment bundle without local accounts, uploads, reports or secrets."""
from pathlib import Path
import shutil

BASE=Path(__file__).resolve().parents[1]
TARGET=BASE/'.vercel-deploy'
TARGET.mkdir(exist_ok=True)
for name in ('backend','config','web'):
    shutil.copytree(BASE/name,TARGET/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
(TARGET/'data').mkdir(exist_ok=True)
for source in (BASE/'data').iterdir():
    if source.suffix in ('.json','.txt'):
        shutil.copy2(source,TARGET/'data'/source.name)
for name in ('server.py','vercel.json'):
    shutil.copy2(BASE/name,TARGET/name)
shutil.copy2(BASE/'requirements-vercel.txt',TARGET/'requirements.txt')
(TARGET/'.python-version').write_text('3.12\n')
(TARGET/'.vercelignore').write_text('.env*\n*.db\n**/__pycache__/\n')
print(f'Prepared Vercel source: {TARGET}')
