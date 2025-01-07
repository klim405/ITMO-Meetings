from typing import Annotated, List

from fastapi import APIRouter, HTTPException, Path, status

import app.schemas.user as schemas
from app.api.deps import AccessTokenDep
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
async def create_user(db: DBSessionDep, creating_data: schemas.CreateUser):
    new_user = await User.create(db, creating_data)
    return new_user


@router.get(
    "/me/",
    name="Получить текущего пользователя",
    description="Возвращает текущего (авторизованного) пользователя.",
    response_model=schemas.ReadUser,
)
async def get_curr_user(db: DBSessionDep, token: AccessTokenDep):
    return await User.get(db, id=token.user_id)


@router.patch(
    "/me/password/",
    name="Сменить пароль текущему пользователю",
    description="Устанавливает новый пароль текущему пользователю.",
    response_model=schemas.ReadUser,
)
async def change_user_password(
    db: DBSessionDep,
    token: AccessTokenDep,
    new_password: schemas.ChangeUserPassword,
):
    curr_user = await User.get(db, id=token.user_id)
    await curr_user.update(db, new_password)
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
async def deactivate_curr_user(db: DBSessionDep, token: AccessTokenDep):
    user = await User.get(db, id=token.user_id)
    await utils.deactivate_user(db, user)


@router.get(
    "/me/channels/",
    name="Получить мои каналы",
    description="Возвращает все экземпляры сущности участник канала с вложенным в нее сообществом (каналом). "
    "В выборку попадают все сообщества (каналы) где текущий пользователь участник или подписчик.",
    response_model=List[ChannelMemberWithChannel],
)
async def get_my_channels(db: DBSessionDep, token: AccessTokenDep):
    return await ChannelMember.filter(db, ChannelMember.user_id == token.user_id)


@router.get(
    "/list/",
    name="Получить список пользователей",
    description="Возвращает список пользователей. Если текущий пользователь администратор, "
    "то все конфиденциальные поля НЕ скрыты, иначе значение этих полей установлены в null.",
    response_model=List[schemas.ReadOpenUserInfo],
)
async def get_user_list(db: DBSessionDep, token: AccessTokenDep):
    user_list = await User.get_all(db)
    if token.is_staff:
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
async def get_user(
    db: DBSessionDep,
    token: AccessTokenDep,
    user_id: Annotated[int, Path(ge=1, examples=[1])],
):
    user = await get_or_404(User, db, id=user_id)
    if token.is_staff or token.user_id == user_id:
        return user
    return schemas.get_open_user_info(user)


@router.put(
    "/{user_id}/",
    name="Изменить пользователя",
    description="Обновляет все обязательные поля.",
    response_model=schemas.ReadUser,
)
async def update_user(
    db: DBSessionDep,
    token: AccessTokenDep,
    user_id: Annotated[int, Path(ge=1, examples=[1])],
    updating_data: schemas.UpdateUser,
):
    user = await get_or_404(User, db, id=user_id)
    if not token.is_staff and user.id != token.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to update user."
        )
    await user.update(db, updating_data)
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
async def deactivate_user(
    db: DBSessionDep,
    token: AccessTokenDep,
    user_id: Annotated[int, Path(ge=1, examples=[1])],
):
    user = await get_or_404(User, db, id=user_id)
    if not token.is_staff and user.id != token.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to deactivate user.",
        )
    await utils.deactivate_user(db, user)
    await user.save(db)


@router.get(
    "/me/meetings/",
    name="Получит связанные со мной мероприятия",
    description="Возвращает все мероприятия в которых текущий пользователь является участником.",
    response_model=List[ReadMeeting],
)
async def get_my_meeting(db: DBSessionDep, token: AccessTokenDep):
    curr_user = await User.get(db, id=token.user_id)
    return await curr_user.awaitable_attrs.meetings
