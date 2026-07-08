from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

StatusEnum = Literal["planned", "ongoing", "done"]
IntensityEnum = Literal["low", "medium", "high"]
SubjectEnum = Literal["Data", "Web", "Systems", "AI", "Other"]

class StudySessionCreate(BaseModel):
    topic: str = Field(..., min_length=1, max_length=100)
    notes: Optional[str] = None
    status: StatusEnum = "planned"
    intensity: IntensityEnum = "medium"
    scheduledFor: datetime
    subject: SubjectEnum

class StudySessionUpdate(BaseModel):
    topic: Optional[str] = Field(None, min_length=1, max_length=100)
    notes: Optional[str] = None
    status: Optional[StatusEnum] = None
    intensity: Optional[IntensityEnum] = None
    scheduledFor: Optional[datetime] = None
    subject: Optional[SubjectEnum] = None

class StudySessionOut(BaseModel):
    id: str
    topic: str
    notes: Optional[str] = None
    status: StatusEnum
    intensity: IntensityEnum
    scheduledFor: datetime
    subject: SubjectEnum
    createdAt: datetime
    updatedAt: datetime