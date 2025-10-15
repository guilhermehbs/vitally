import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.db.db import Base, SessionLocal, engine  # noqa: E402

load_dotenv(dotenv_path=ROOT / ".env")

if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL não encontrado no .env")


@pytest.fixture(autouse=True)
def clean_db():
    from src.db.db import engine
    from src.db.tables import PacienteSQL

    table_name = PacienteSQL.__table__.name

    with engine.begin() as conn:
        if engine.dialect.name == "sqlite":
            conn.exec_driver_sql(f'DELETE FROM "{table_name}";')
            try:
                conn.exec_driver_sql(f"DELETE FROM sqlite_sequence WHERE name='{table_name}';")
            except Exception:
                pass
        else:
            conn.exec_driver_sql(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE;')
    yield


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="session", autouse=True)
def _create_drop_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
