import os, sys, pytest

from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

load_dotenv(dotenv_path=ROOT / ".env")

if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL não encontrado no .env")

from src.db import Base, engine, SessionLocal

@pytest.fixture(autouse=True)
def clean_db():
    from src.db import engine
    from src.models_sql import PacienteSQL

    table = PacienteSQL.__table__
    table_name = table.name

    with engine.begin() as conn:
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
