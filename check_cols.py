import sys
sys.path.insert(0, '.')
from scripts.config import DB_URI_POOLED_SA
from sqlalchemy import create_engine, text

engine = create_engine(DB_URI_POOLED_SA)
with engine.connect() as conn:
    q = text("SELECT column_name FROM information_schema.columns WHERE table_name='fact_transactions' ORDER BY ordinal_position")
    rows = conn.execute(q).fetchall()
    print("fact_transactions columns:")
    for r in rows:
        print(" -", r[0])
