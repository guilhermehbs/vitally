import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.db import SessionLocal  # noqa: E402
from src.db.tables import UserSQL  # noqa: E402
from src.security.auth import hash_password  # noqa: E402

with SessionLocal() as s:
    user = UserSQL(
        email="",
        name="",
        password_hash=hash_password(""),
        is_active=True,
    )
    s.add(user)
    s.commit()
