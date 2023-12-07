from typing import Annotated, List

from fastapi import APIRouter, Path, Depends, HTTPException, status

import app.schemas.user as schemas
from app.auth.deps import get_current_user, UserInfo
from app.database.deps import DBSessionDep
from app.database.utils import get_or_404
from app.models import User, utils, ChannelMember
from app.schemas.complex_schemas import ChannelMemberWithChannel

router = APIRouter()


@router.post('/', response_model=schemas.ReadUser)
def create_user(
        db: DBSessionDep,
        creating_data: schemas.CreateUser
):
    new_user = User.create(db, creating_data)
    return new_user


@router.get('/me/', name='Get current User',
            response_model=schemas.ReadUser)
def get_curr_user(
        db: DBSessionDep,
        user: Annotated[UserInfo, Depends(get_current_user)]
):
    return user.get_model(db)


@router.patch('/me/password/',
              response_model=schemas.ReadUser)
def change_user_password(
        db: DBSessionDep,
        curr_user_info: Annotated[UserInfo, Depends(get_current_user)],
        new_password: schemas.ChangeUserPassword
):
    curr_user = curr_user_info.get_model(db)
    curr_user.update(db, new_password)
    return curr_user


@router.delete('/me/', name='Deactivate current User')
def deactivate_curr_user(
        db: DBSessionDep,
        user_info: Annotated[UserInfo, Depends(get_current_user)]
):
    user = user_info.get_model(db)
    utils.deactivate_user(db, user)


@router.get('/me/channels/',
            description="Returned channels to which current user is subscribed.",
            response_model=List[ChannelMemberWithChannel])
def get_my_channels(
        db: DBSessionDep,
        user_info: Annotated[UserInfo, Depends(get_current_user)]
):
    return ChannelMember.filter(db, ChannelMember.user_id == user_info.id)


@router.get('/list/', response_model=List[schemas.ReadOpenUserInfo])
def get_user_list(
        db: DBSessionDep,
        curr_user: Annotated[UserInfo, Depends(get_current_user)]
):
    user_list = User.get_all(db)
    if curr_user.is_staff:
        return user_list
    return map(schemas.get_open_user_info, user_list)


@router.get('/{user_id}/',
            description='This operation will return User. '
                        'If current user is not target user or has not staff access, '
                        'then request wont contain private information (fields).',
            response_model=schemas.ReadOpenUserInfo)
def get_user(
        db: DBSessionDep,
        curr_user: Annotated[UserInfo, Depends(get_current_user)],
        user_id: Annotated[int, Path(ge=1, examples=[1])]
):
    user = get_or_404(User, db, id=user_id)
    if curr_user.is_staff or curr_user.id == user_id:
        return user
    return schemas.get_open_user_info(user)


@router.put('/{user_id}/',
            description='This operation will update all required fields.',
            response_model=schemas.ReadUser)
def update_user(
        db: DBSessionDep,
        curr_user: Annotated[User, Depends(get_current_user)],
        user_id: Annotated[int, Path(ge=1, examples=[1])],
        updating_data: schemas.UpdateUser
):
    user = get_or_404(User, db, id=user_id)
    if not curr_user.is_staff and user.id != curr_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You do not have access to update user.')
    user.update(db, updating_data)
    return user


@router.delete('/{user_id}/',
               description='This operation will update all required fields.')
def deactivate_user(
        db: DBSessionDep,
        curr_user: Annotated[User, Depends(get_current_user)],
        user_id: Annotated[int, Path(ge=1, examples=[1])]
):
    user = get_or_404(User, db, id=user_id)
    if not curr_user.is_staff and user.id != curr_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You do not have access to deactivate user.')
    utils.deactivate_user(db, user)
    user.save(db)
