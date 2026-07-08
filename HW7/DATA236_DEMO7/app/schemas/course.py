from pydantic import BaseModel, Field


class CourseCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)


class CourseResponse(BaseModel):
    id: int
    title: str
    instructor: str
