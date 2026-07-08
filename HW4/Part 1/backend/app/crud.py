from sqlalchemy.orm import Session
from . import models, schema
from datetime import datetime, timedelta, timezone
import hashlib

def hash_password(password: str) ->  str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash

def create_user(db: Session, payload: schema.UserCreate):
    user = models.User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_users(db: Session):
    return db.query(models.User).order_by(models.User.id.asc()).all()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_book(db: Session, payload: schema.BookCreate):
    book = models.Book(title=payload.title, author=payload.author)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book

def get_books(db: Session):
    return db.query(models.Book).order_by(models.Book.id.asc()).all()

def get_book(db: Session, book_id: int):
    return db.query(models.Book).filter(models.Book.id == book_id).first()

def update_book(db: Session, book_id: int, payload: schema.BookUpdate):
    book = get_book(db, book_id)
    if not book:
        return None
    book.title = payload.title
    book.author = payload.author
    db.commit()
    db.refresh(book)
    return book

def delete_book(db: Session, book_id: int):
    book = get_book(db, book_id)
    if not book:
        return None
    db.delete(book)
    db.commit()
    return book



