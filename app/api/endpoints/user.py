from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Path, status

import app.schemas.user as schemas
from app.auth.deps import UserInfo, get_current_user
from app.database.deps import DBSessionDep
from app.database.utils import get_or_404
from app.models import ChannelMember, User, utils
from app.schemas.complex_schemas import ChannelMemberWithChannel
from app.schemas.meeting import ReadMeeting

router = APIRouter()


@router.post(
    "/",
    name="Зарегистрировать пользователя",
    description="Регистрирует пользователя. Если возникает валидационная ошибка, "
    "либо какое-то уникальное поле не уникально, то возвращается HTTP 422 (Не обрабатываемая сущность)",
    response_model=schemas.ReadUser,
)
def create_user(db: DBSessionDep, creating_data: schemas.CreateUser):
    new_user = User.create(db, creating_data)
    return new_user


@router.get(
    "/me/",
    name="Получить текущего пользователя",
    description="Возвращает текущего (авторизованного) пользователя.",
    response_model=schemas.ReadUser,
)
def get_curr_user(db: DBSessionDep, user: Annotated[UserInfo, Depends(get_current_user)]):
    return user.get_model(db)


@router.patch(
    "/me/password/",
    name="Сменить пароль текущему пользователю",
    description="Устанавливает новый пароль текущему пользователю.",
    response_model=schemas.ReadUser,
)
def change_user_password(
    db: DBSessionDep,
    curr_user_info: Annotated[UserInfo, Depends(get_current_user)],
    new_password: schemas.ChangeUserPassword,
):
    curr_user = curr_user_info.get_model(db)
    curr_user.update(db, new_password)
    return curr_user


@router.delete(
    "/me/",
    name="Деактивирует текущего пользователя",
    description="Выполняет процесс деактивации пользователя, "
    "после данного действия пользователь не сможет авторизоваться в системе, "
    "также пользователь исключается из всех сообществ где он является участником. "
    "Если пользователь владеет сообществом, то его права владельца передаются другому участнику сообщества"
    " с наиболее высоким уровнем доступа. "
    "Если пользователь владелец и является единственным участником сообщества, "
    "то сообщество деактивируется, в дальнейшем владелец может его восстановить. "
    "Личное сообщество (канал) деактивируется.",
)
def deactivate_curr_user(db: DBSessionDep, user_info: Annotated[UserInfo, Depends(get_current_user)]):
    user = user_info.get_model(db)
    utils.deactivate_user(db, user)


@router.get(
    "/me/channels/",
    name="Получить мои каналы",
    description="Возвращает все экземпляры сущности участник канала с вложенным в нее сообществом (каналом). "
    "В выборку попадают все сообщества (каналы) где текущий пользователь участник или подписчик.",
    response_model=List[ChannelMemberWithChannel],
)
def get_my_channels(db: DBSessionDep, user_info: Annotated[UserInfo, Depends(get_current_user)]):
    return ChannelMember.filter(db, ChannelMember.user_id == user_info.id)


@router.get(
    "/list/",
    name="Получить список пользователей",
    description="Возвращает список пользователей. Если текущий пользователь администратор, "
    "то все конфиденциальные поля НЕ скрыты, иначе значение этих полей установлены в null.",
    response_model=List[schemas.ReadOpenUserInfo],
)
def get_user_list(db: DBSessionDep, curr_user: Annotated[UserInfo, Depends(get_current_user)]):
    user_list = User.get_all(db)
    if curr_user.is_staff:
        return user_list
    return map(schemas.get_open_user_info, user_list)


@router.get(
    "/{user_id}/",
    name="Получить пользователя.",
    description="Возвращает сущность пользователя. "
    "Если текущий пользователь НЕ является администратором, "
    "то конфиденциальные поля установлены в null.",
    response_model=schemas.ReadOpenUserInfo,
)
def get_user(
    db: DBSessionDep,
    curr_user: Annotated[UserInfo, Depends(get_current_user)],
    user_id: Annotated[int, Path(ge=1, examples=[1])],
):
    user = get_or_404(User, db, id=user_id)
    if curr_user.is_staff or curr_user.id == user_id:
        return user
    return schemas.get_open_user_info(user)


@router.put(
    "/{user_id}/",
    name="Изменить пользователя",
    description="Обновляет все обязательные поля.",
    response_model=schemas.ReadUser,
)
def update_user(
    db: DBSessionDep,
    curr_user: Annotated[User, Depends(get_current_user)],
    user_id: Annotated[int, Path(ge=1, examples=[1])],
    updating_data: schemas.UpdateUser,
):
    user = get_or_404(User, db, id=user_id)
    if not curr_user.is_staff and user.id != curr_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to update user."
        )
    user.update(db, updating_data)
    return user


@router.delete(
    "/{user_id}/",
    name="Удалить пользователя",
    description="Данная операция доступна только администратору. "
    "Выполняет процесс деактивации пользователя, "
    "после данного действия пользователь не сможет авторизоваться в системе, "
    "также пользователь исключается из всех сообществ где он является участником. "
    "Если пользователь владеет сообществом, то его права владельца передаются другому участнику сообщества"
    " с наиболее высоким уровнем доступа. "
    "Если пользователь владелец и является единственным участником сообщества, "
    "то сообщество деактивируется, в дальнейшем владелец может его восстановить. "
    "Личное сообщество (канал) деактивируется.",
)
def deactivate_user(
    db: DBSessionDep,
    curr_user: Annotated[User, Depends(get_current_user)],
    user_id: Annotated[int, Path(ge=1, examples=[1])],
):
    user = get_or_404(User, db, id=user_id)
    if not curr_user.is_staff and user.id != curr_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to deactivate user.",
        )
    utils.deactivate_user(db, user)
    user.save(db)


@router.get(
    "/me/meetings/",
    name="Получит связанные со мной мероприятия",
    description="Возвращает все мероприятия в которых текущий пользователь является участником.",
    response_model=List[ReadMeeting],
)
def get_my_meeting(db: DBSessionDep, user_info: Annotated[UserInfo, Depends(get_current_user)]):
    curr_user = user_info.get_model(db)
    return curr_user.meetings
