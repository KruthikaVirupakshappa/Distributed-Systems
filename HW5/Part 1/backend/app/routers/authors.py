from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from ..deps import get_db
from .. import schemas, crud

router = APIRouter(prefix="/authors", tags=["Authors"])


@router.post("", response_model=schemas.AuthorOut, status_code=201)
def create(payload: schemas.AuthorCreate, db: Session = Depends(get_db)):
    return crud.create_author(db, payload)


@router.get("", response_model=List[schemas.AuthorOut])
def list_(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return crud.list_authors(db, skip, limit)


@router.get("/{author_id}", response_model=schemas.AuthorOut)
def get_(author_id: int, db: Session = Depends(get_db)):
    return crud.get_author(db, author_id)


@router.put("/{author_id}", response_model=schemas.AuthorOut)
def update(author_id: int, payload: schemas.AuthorUpdate, db: Session = Depends(get_db)):
    return crud.update_author(db, author_id, payload)


@router.delete("/{author_id}", status_code=204)
def delete(author_id: int, db: Session = Depends(get_db)):
    crud.delete_author(db, author_id)