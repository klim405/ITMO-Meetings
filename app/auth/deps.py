from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.auth.schemas import TokenData
from app.database.core import SessionLocal
from app.database.utils import get_or_404
from app.models import User
from app.settings import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class UserInfo:
    def __init__(self, user: User):
        self.id = user.id
        self.is_staff = user.is_staff

    def get_model(self, db_session: Session) -> User:
        return get_or_404(User, db_session, id=self.id)


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    with SessionLocal() as db_session:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.TOKEN_CIPHER_ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise token_exception
            token_data = TokenData(user_id=user_id)
        except JWTError:
            raise token_exception
        user = User.get(db_session, id=token_data.user_id)
        if user is None:
            raise token_exception
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
        return UserInfo(user)


login_required = Depends(get_current_user)
CurrentUserDep = Annotated[UserInfo, Depends(get_current_user)]
