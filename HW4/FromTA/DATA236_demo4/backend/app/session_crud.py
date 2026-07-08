from datetime import datetime, timedelta
import secrets
from sqlalchemy.orm import Session
from .models import SessionToken

SESSION_TTL_MINUTES = 30

def create_session(db: Session, user_id: int) -> SessionToken:
    token = secrets.token_hex(32)
    expires = datetime.utcnow() + timedelta(minutes=SESSION_TTL_MINUTES)  # ✅ naive UTC

    row = SessionToken(id=token, user_id=user_id, expires_at=expires)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

def get_session(db: Session, token: str) -> SessionToken | None:
    s = db.query(SessionToken).filter(SessionToken.id == token).first()
    if not s:
        return None

    # ✅ compare naive-to-naive
    if s.expires_at < datetime.utcnow():
        db.delete(s)
        db.commit()
        return None

    return s

def delete_session(db: Session, token: str) -> bool:
    s = db.query(SessionToken).filter(SessionToken.id == token).first()
    if not s:
        return False
    db.delete(s)
    db.commit()
    return True