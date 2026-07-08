from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

TaskStatus = Literal["pending", "in-progress", "completed"]
TaskPriority = Literal["low", "medium", "high"]
TaskCategory = Literal["Work", "Personal", "Shopping", "Health", "Other"]
MessageRole = Literal["user", "assistant"]
SummaryScope = Literal["session", "user"]


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None)
    status: TaskStatus = "pending"
    priority: TaskPriority = "medium"
    dueDate: datetime
    category: TaskCategory


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    dueDate: Optional[datetime] = None
    category: Optional[TaskCategory] = None


class TaskOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    dueDate: datetime
    category: TaskCategory
    createdAt: datetime
    updatedAt: datetime


class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    session_id: Optional[str] = Field(default=None, min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str
    memory_used: dict


class MessageOut(BaseModel):
    role: MessageRole
    content: str
    created_at: datetime


class SummaryOut(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    scope: SummaryScope
    text: str
    created_at: datetime


class EpisodeOut(BaseModel):
    fact: str
    importance: float = Field(ge=0.0, le=1.0)
    created_at: datetime


class MemoryViewResponse(BaseModel):
    user_id: str
    session_id: str
    recent_messages: list[MessageOut]
    latest_session_summary: Optional[SummaryOut] = None
    latest_lifetime_summary: Optional[SummaryOut] = None
    recent_episodes: list[EpisodeOut]


class AggregateResponse(BaseModel):
    user_id: str
    daily_message_counts: list[dict]
    recent_summaries: list[SummaryOut]
