from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models.user import UserInDB
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: UserInDB = Depends(get_current_user)):
    return current_user
