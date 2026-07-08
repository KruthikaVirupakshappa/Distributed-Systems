from pydantic import BaseModel


class Course(BaseModel):
    id: int
    title: str
    instructor: str
