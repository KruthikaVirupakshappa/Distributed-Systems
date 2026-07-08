from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user, require_roles
from app.db.fake_db import fake_courses_db
from app.models.user import UserInDB
from app.schemas.course import CourseCreate, CourseResponse

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("", response_model=list[CourseResponse])
def get_courses(current_user: UserInDB = Depends(get_current_user)):
    return fake_courses_db


@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_course(
    course: CourseCreate,
    current_user: UserInDB = Depends(require_roles(["instructor", "admin"])),
):
    new_id = max((c["id"] for c in fake_courses_db), default=0) + 1
    new_course = {
        "id": new_id,
        "title": course.title,
        "instructor": current_user.username,
    }
    fake_courses_db.append(new_course)
    return new_course


@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    current_user: UserInDB = Depends(require_roles(["admin"])),
):
    for index, course in enumerate(fake_courses_db):
        if course["id"] == course_id:
            deleted = fake_courses_db.pop(index)
            return {
                "message": "Course deleted successfully",
                "deleted_course": deleted,
                "deleted_by": current_user.username,
            }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Course not found",
    )
