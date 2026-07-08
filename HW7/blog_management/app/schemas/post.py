from datetime import datetime

from pydantic import BaseModel


class PostCreate(BaseModel):
    title: str
    content: str


class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    author: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
