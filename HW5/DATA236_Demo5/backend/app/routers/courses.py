from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from ..deps import get_db
from .. import schemas, crud

router = APIRouter(prefix="/courses", tags=["Courses"])

@router.post("", response_model=schemas.CourseOut, status_code=201)
def create(payload: schemas.CourseCreate, db: Session = Depends(get_db)):
    return crud.create_course(db, payload)

@router.get("", response_model=List[schemas.CourseOut])
def list_(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return crud.list_courses(db, skip, limit)

@router.get("/{course_id}", response_model=schemas.CourseOut)
def get_(course_id: int, db: Session = Depends(get_db)):
    return crud.get_course(db, course_id)

@router.put("/{course_id}", response_model=schemas.CourseOut)
def update(course_id: int, payload: schemas.CourseUpdate, db: Session = Depends(get_db)):
    return crud.update_course(db, course_id, payload)

@router.delete("/{course_id}", status_code=204)
def delete(course_id: int, db: Session = Depends(get_db)):
    crud.delete_course(db, course_id)

# extra endpoint (like “books by author”)
@router.get("/by-instructor/{instructor_id}", response_model=List[schemas.CourseOut])
def by_instructor(instructor_id: int, db: Session = Depends(get_db)):
    return crud.courses_by_instructor(db, instructor_id)