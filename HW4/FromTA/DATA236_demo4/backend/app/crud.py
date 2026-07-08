from sqlalchemy.orm import Session
from . import models, schema
from datetime import datetime, timedelta, timezone


def create_user(db: Session, payload: schema.UserCreate):
    user = models.User(name=payload.name, email=payload.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_users(db: Session):
    return db.query(models.User).order_by(models.User.id.asc()).all()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def update_user(db: Session, user_id: int, payload: schema.UserUpdate):
    user = get_user(db, user_id)
    if not user:
        return None
    user.name = payload.name
    user.email = payload.email
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int):
    user = get_user(db, user_id)
    if not user:
        return None
    db.delete(user)
    db.commit()
    return user


