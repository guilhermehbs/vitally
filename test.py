import bcrypt

from src.db.db import SessionLocal
from src.db.tables import UserSQL

senha = "admin1009"
hashed = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode()

with SessionLocal() as session:
    novo_usuario = UserSQL(
        email="admin@vitally.com", name="admin", password_hash=hashed, is_active=True
    )
    session.add(novo_usuario)
    session.commit()
