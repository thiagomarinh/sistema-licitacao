"""
Copia os dados do composicoes.db (SQLite) para o Postgres do Supabase.

Uso:
    1. Defina SUPABASE_DATABASE_URL no .env ou no ambiente, com a connection
       string do Supabase (Settings > Database > Connection string > URI).
    2. Rode: python scripts/migrar_para_supabase.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import db, Empresa, Composicao, Declaracao, Documento

SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'composicoes.db')
SQLITE_URL = f'sqlite:///{SQLITE_PATH}'

pg_url = os.environ.get('SUPABASE_DATABASE_URL', '')
if pg_url.startswith('postgres://'):
    pg_url = pg_url.replace('postgres://', 'postgresql://', 1)
if not pg_url:
    print('Defina SUPABASE_DATABASE_URL antes de rodar este script.')
    sys.exit(1)

src_engine = create_engine(SQLITE_URL)
dst_engine = create_engine(pg_url)

db.metadata.create_all(dst_engine)

SrcSession = sessionmaker(bind=src_engine)
DstSession = sessionmaker(bind=dst_engine)
src = SrcSession()
dst = DstSession()

for Model in [Empresa, Composicao, Declaracao, Documento]:
    rows = src.query(Model).all()
    for row in rows:
        src.expunge(row)
        dst.merge(row)
    dst.commit()
    print(f'{Model.__tablename__}: {len(rows)} registro(s) migrado(s)')

print('Migração concluída.')
