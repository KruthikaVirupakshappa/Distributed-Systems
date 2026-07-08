from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# -------- Instructors --------
class InstructorCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr

class InstructorUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None

class InstructorOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


# -------- Courses --------
class CourseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=3, max_length=20)
    year: int = Field(ge=0, le=2100)
    seats_available: int = Field(ge=0, default=30)
    instructor_id: int = Field(gt=0)

class CourseUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    code: Optional[str] = Field(default=None, min_length=3, max_length=20)
    year: Optional[int] = Field(default=None, ge=0, le=2100)
    seats_available: Optional[int] = Field(default=None, ge=0)
    instructor_id: Optional[int] = Field(default=None, gt=0)

class CourseOut(BaseModel):
    id: int
    title: str
    code: str
    year: int
    seats_available: int
    instructor_id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True