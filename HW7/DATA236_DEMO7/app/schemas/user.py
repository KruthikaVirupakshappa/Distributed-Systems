from pydantic import BaseModel


class UserResponse(BaseModel):
    username: str
    full_name: str
    role: str
    disabled: bool
