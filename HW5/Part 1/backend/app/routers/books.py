from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from ..deps import get_db
from .. import schemas, crud

router = APIRouter(prefix="/books", tags=["Books"])


@router.post("", response_model=schemas.BookOut, status_code=201)
def create(payload: schemas.BookCreate, db: Session = Depends(get_db)):
    return crud.create_book(db, payload)


@router.get("", response_model=List[schemas.BookOut])
def list_(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return crud.list_books(db, skip, limit)


@router.get("/{book_id}", response_model=schemas.BookOut)
def get_(book_id: int, db: Session = Depends(get_db)):
    return crud.get_book(db, book_id)


@router.put("/{book_id}", response_model=schemas.BookOut)
def update(book_id: int, payload: schemas.BookUpdate, db: Session = Depends(get_db)):
    return crud.update_book(db, book_id, payload)


@router.delete("/{book_id}", status_code=204)
def delete(book_id: int, db: Session = Depends(get_db)):
    crud.delete_book(db, book_id)


# extra endpoint: all books by a specific author
@router.get("/by-author/{author_id}", response_model=List[schemas.BookOut])
def by_author(author_id: int, db: Session = Depends(get_db)):
    return crud.books_by_author(db, author_id)