from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from . import models, schemas

# ---------- Authors ----------
def create_author(db: Session, payload: schemas.AuthorCreate):
    author = models.Author(**payload.model_dump())
    db.add(author)
    try:
        db.commit()
        db.refresh(author)
        return author
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Author email must be unique.")


def list_authors(db: Session, skip: int, limit: int):
    return (
        db.scalars(
            select(models.Author)
            .offset(skip)
            .limit(limit)
            .order_by(models.Author.id)
        )
        .all()
    )


def get_author(db: Session, author_id: int):
    author = db.get(models.Author, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found.")
    return author


def update_author(db: Session, author_id: int, payload: schemas.AuthorUpdate):
    author = get_author(db, author_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(author, k, v)
    try:
        db.commit()
        db.refresh(author)
        return author
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Author email must be unique.")


def delete_author(db: Session, author_id: int):
    author = get_author(db, author_id)
    count = db.scalar(
        select(func.count(models.Book.id)).where(models.Book.author_id == author_id)
    )
    if count and count > 0:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete author with associated books.",
        )
    db.delete(author)
    db.commit()


# ---------- Books ----------
def create_book(db: Session, payload: schemas.BookCreate):
    # Ensure referenced author exists
    if not db.get(models.Author, payload.author_id):
        raise HTTPException(
            status_code=404,
            detail="Author not found for author_id.",
        )
    book = models.Book(**payload.model_dump())
    db.add(book)
    try:
        db.commit()
        db.refresh(book)
        return book
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Book ISBN must be unique.",
        )


def list_books(db: Session, skip: int, limit: int):
    return (
        db.scalars(
            select(models.Book)
            .offset(skip)
            .limit(limit)
            .order_by(models.Book.id)
        )
        .all()
    )


def get_book(db: Session, book_id: int):
    book = db.get(models.Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")
    return book


def update_book(db: Session, book_id: int, payload: schemas.BookUpdate):
    book = get_book(db, book_id)
    data = payload.model_dump(exclude_unset=True)

    # If author_id is changing, ensure the new author exists
    if "author_id" in data and not db.get(models.Author, data["author_id"]):
        raise HTTPException(
            status_code=404,
            detail="Author not found for author_id.",
        )

    for k, v in data.items():
        setattr(book, k, v)
    try:
        db.commit()
        db.refresh(book)
        return book
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Book ISBN must be unique.",
        )


def delete_book(db: Session, book_id: int):
    book = get_book(db, book_id)
    db.delete(book)
    db.commit()


def books_by_author(db: Session, author_id: int):
    if not db.get(models.Author, author_id):
        raise HTTPException(status_code=404, detail="Author not found.")
    return (
        db.scalars(
            select(models.Book)
            .where(models.Book.author_id == author_id)
            .order_by(models.Book.id)
        )
        .all()
    )