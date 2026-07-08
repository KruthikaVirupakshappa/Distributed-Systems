"""Seed the database with the blog_db schema and initial users."""

import sys

# ---------------------------------------------------------------------------
# 1. Ensure the database exists (connect without DB name first)
# ---------------------------------------------------------------------------
import pymysql  # noqa: E402

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.database import Base, SessionLocal, engine

try:
    conn = pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
    )
    with conn.cursor() as cur:
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        )
    conn.commit()
    conn.close()
    print(f"Database '{settings.DB_NAME}' ready.")
except Exception as exc:
    print(f"ERROR: Could not connect to MySQL — {exc}")
    print("Make sure MySQL is running and .env credentials are correct.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 2. Create all tables
# ---------------------------------------------------------------------------
# Import models so SQLAlchemy registers them with Base
from app.models.post import Post  # noqa: F401, E402
from app.models.user import User  # noqa: F401, E402

Base.metadata.create_all(bind=engine)
print("Tables created (users, posts).")

# ---------------------------------------------------------------------------
# 3. Seed users
# ---------------------------------------------------------------------------
SEED_USERS = [
    {"username": "alice", "password": "alice123", "role": "reader"},
    {"username": "bob", "password": "bob123", "role": "writer"},
    {"username": "carol", "password": "carol123", "role": "moderator"},
]

db = SessionLocal()
try:
    for u in SEED_USERS:
        existing = db.query(User).filter(User.username == u["username"]).first()
        if existing:
            print(f"  User '{u['username']}' already exists — skipping.")
        else:
            user = User(
                username=u["username"],
                hashed_password=get_password_hash(u["password"]),
                role=u["role"],
            )
            db.add(user)
            print(f"  Created user '{u['username']}' with role '{u['role']}'.")
    db.commit()
finally:
    db.close()

print("\nSeed complete. Users:")
print("  alice / alice123  → reader")
print("  bob   / bob123    → writer")
print("  carol / carol123  → moderator")
