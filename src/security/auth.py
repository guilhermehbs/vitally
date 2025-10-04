import bcrypt

from src.db.db import SessionLocal
from src.db.tables import UserSQL


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def get_user_by_email(email: str) -> UserSQL | None:
    with SessionLocal() as s:
        return s.query(UserSQL).filter(UserSQL.email == email, UserSQL.is_active.is_(True)).first()
