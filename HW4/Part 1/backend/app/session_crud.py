import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from . import models

SESSION_MINUTES = 30


def create_session(db: Session, user_id: int):
    token = secrets.token_hex(32)
    now = datetime.utcnow()
    expires = now + timedelta(minutes=SESSION_MINUTES)

    s = models.Session(
        id=token,
        user_id=user_id,
        created_at=now,
        expires_at=expires,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def get_session(db: Session, token: str):
    s = db.query(models.Session).filter(models.Session.id == token).first()
    if not s:
        return None

    if s.expires_at <= datetime.utcnow():
        db.delete(s)
        db.commit()
        return None

    return s


def delete_session(db: Session, token: str):
    s = db.query(models.Session).filter(models.Session.id == token).first()
    if not s:
        return
    db.delete(s)
    db.commit()
