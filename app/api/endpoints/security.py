from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status

from app.database.deps import DBSessionDep
from app.models import User
from app.schemas.token import TokenResponse
from app.utils.security import create_access_token

router = APIRouter()


@router.post("/token")
async def create_token(
    db_session: DBSessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> TokenResponse:
    user = await User.get_by_login(db_session, form_data.username)
    if user is None or not user.verify_password(form_data.password) or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong login",
            headers={"WWW-Authenticate": "Bearer"},
        )
    resp = TokenResponse(access_token=create_access_token(user))
    return resp
