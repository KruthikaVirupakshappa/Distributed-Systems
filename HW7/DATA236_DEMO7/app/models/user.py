from pydantic import BaseModel


class User(BaseModel):
    username: str
    full_name: str
    role: str
    disabled: bool = False


class UserInDB(User):
    hashed_password: str
