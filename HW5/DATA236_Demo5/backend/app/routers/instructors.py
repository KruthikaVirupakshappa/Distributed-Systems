from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/instructors", tags=["Instructors"])


@router.post("", response_model=schemas.InstructorOut, status_code=status.HTTP_201_CREATED)
def create_instructor(payload: schemas.InstructorCreate, db: Session = Depends(get_db)):
    instructor = models.Instructor(**payload.model_dump())
    db.add(instructor)
    try:
        db.commit()
        db.refresh(instructor)
        return instructor
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Instructor email must be unique.")


@router.get("", response_model=list[schemas.InstructorOut])
def list_instructors(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return db.query(models.Instructor).offset(skip).limit(limit).all()


@router.get("/{instructor_id}", response_model=schemas.InstructorOut)
def get_instructor(instructor_id: int, db: Session = Depends(get_db)):
    inst = db.query(models.Instructor).filter(models.Instructor.id == instructor_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instructor not found.")
    return inst


@router.put("/{instructor_id}", response_model=schemas.InstructorOut)
def update_instructor(instructor_id: int, payload: schemas.InstructorUpdate, db: Session = Depends(get_db)):
    inst = db.query(models.Instructor).filter(models.Instructor.id == instructor_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instructor not found.")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(inst, k, v)

    try:
        db.commit()
        db.refresh(inst)
        return inst
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Instructor email must be unique.")


@router.delete("/{instructor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_instructor(instructor_id: int, db: Session = Depends(get_db)):
    inst = db.query(models.Instructor).filter(models.Instructor.id == instructor_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instructor not found.")

    # prevent deletion if courses exist (assignment requirement)
    course_count = db.query(models.Course).filter(models.Course.instructor_id == instructor_id).count()
    if course_count > 0:
        raise HTTPException(status_code=409, detail="Cannot delete instructor with associated courses.")

    db.delete(inst)
    db.commit()
    return