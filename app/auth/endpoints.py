from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app import settings
from app.auth.schemas import Token
from app.auth.utils import authenticate_user, create_access_token
from app.database.deps import DBSessionDep

router = APIRouter()


@router.post("/token", response_model=Token)
async def create_token(db: DBSessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await authenticate_user(db, form_data.username, form_data.password)
    access_token_expires = timedelta(minutes=settings.auth.access_token_lifetime_in_min)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}
