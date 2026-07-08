from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from . import models, schemas

# ---------- Instructors ----------
def create_instructor(db: Session, payload: schemas.InstructorCreate):
    inst = models.Instructor(**payload.model_dump())
    db.add(inst)
    try:
        db.commit()
        db.refresh(inst)
        return inst
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Instructor email must be unique.")

def list_instructors(db: Session, skip: int, limit: int):
    return db.scalars(select(models.Instructor).offset(skip).limit(limit).order_by(models.Instructor.id)).all()

def get_instructor(db: Session, instructor_id: int):
    inst = db.get(models.Instructor, instructor_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instructor not found.")
    return inst

def update_instructor(db: Session, instructor_id: int, payload: schemas.InstructorUpdate):
    inst = get_instructor(db, instructor_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(inst, k, v)
    try:
        db.commit()
        db.refresh(inst)
        return inst
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Instructor email must be unique.")

def delete_instructor(db: Session, instructor_id: int):
    inst = get_instructor(db, instructor_id)
    count = db.scalar(select(func.count(models.Course.id)).where(models.Course.instructor_id == instructor_id))
    if count and count > 0:
        raise HTTPException(status_code=409, detail="Cannot delete instructor with associated courses.")
    db.delete(inst)
    db.commit()


# ---------- Courses ----------
def create_course(db: Session, payload: schemas.CourseCreate):
    if not db.get(models.Instructor, payload.instructor_id):
        raise HTTPException(status_code=404, detail="Instructor not found for instructor_id.")
    c = models.Course(**payload.model_dump())
    db.add(c)
    try:
        db.commit()
        db.refresh(c)
        return c
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Course code must be unique.")

def list_courses(db: Session, skip: int, limit: int):
    return db.scalars(select(models.Course).offset(skip).limit(limit).order_by(models.Course.id)).all()

def get_course(db: Session, course_id: int):
    c = db.get(models.Course, course_id)
    if not c:
        raise HTTPException(status_code=404, detail="Course not found.")
    return c

def update_course(db: Session, course_id: int, payload: schemas.CourseUpdate):
    c = get_course(db, course_id)
    data = payload.model_dump(exclude_unset=True)
    if "instructor_id" in data and not db.get(models.Instructor, data["instructor_id"]):
        raise HTTPException(status_code=404, detail="Instructor not found for instructor_id.")
    for k, v in data.items():
        setattr(c, k, v)
    try:
        db.commit()
        db.refresh(c)
        return c
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Course code must be unique.")

def delete_course(db: Session, course_id: int):
    c = get_course(db, course_id)
    db.delete(c)
    db.commit()

def courses_by_instructor(db: Session, instructor_id: int):
    if not db.get(models.Instructor, instructor_id):
        raise HTTPException(status_code=404, detail="Instructor not found.")
    return db.scalars(select(models.Course).where(models.Course.instructor_id == instructor_id).order_by(models.Course.id)).all()