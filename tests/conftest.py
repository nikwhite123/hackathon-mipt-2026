import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_DB_PATH = ROOT / 'test_app.db'
os.environ['DATABASE_URL'] = f'sqlite:///{TEST_DB_PATH}'
os.environ['AUTO_CREATE_DB'] = 'true'

if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Organization
from app.repositories.data_repository import get_data_repository

Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    if db.query(Organization).first() is None:
        incidents = get_data_repository().load_incidents()
        codes = sorted({str(code) for code in incidents['organization_code'].dropna().astype(str).tolist()})
        for code in codes:
            db.add(Organization(name=f'Организация {code}', code=code))
        db.commit()
