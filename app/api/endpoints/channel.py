from typing import Annotated, List, Literal, Set

from fastapi import APIRouter, Depends, Path, HTTPException, status, Query

from app.api.deps import get_current_channel_member
from app.auth.deps import get_current_user, CurrentUserDep, login_required
from app.database.deps import DBSessionDep
from app.database.utils import get_or_404
from app.models import Channel, ChannelMember
from app.models.channel_member import Role, Permission
from app.models.utils import delete_owner
from app.schemas.channel import ReadChannel, CreateChannel, UpdateChannel, RecoveryChannel
from app.schemas.channel_member import ReadChannelMember, CreateChannelMember, ChannelMemberRole

router = APIRouter()


@router.get(
    '/list/',
    name='Получить список каналов.',
    description='Возвращает все каналы, которые не удалены (активны).',
    dependencies=[login_required],
    response_model=List[ReadChannel])
def get_channel_list(db: DBSessionDep):
    return Channel.filter(db, Channel.is_active == True)


@router.get(
    '/my-personal-channel/',
    name='Вернуть мой канал',
    description='Возвращает канал текущего пользователя.',
    response_model=ReadChannel)
def update_channel(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep
):
    curr_channel_member = ChannelMember.get_first_by_filter(
        db,
        ChannelMember.user_id == curr_user_info.id,
        ChannelMember.is_owner == True,
        ChannelMember.channel.has(is_personal=True)
    )

    if curr_channel_member is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='User has not personal channel.'
    )

    return curr_channel_member.channel


@router.get(
    '/{channel_id}/',
    name='Получить сообщество (канал)',
    response_model=ReadChannel,
    dependencies=[Depends(get_current_user)])
def get_channel(db: DBSessionDep, channel_id: Annotated[int, Path(ge=1)]):
    return get_or_404(Channel, db, id=channel_id)


@router.post(
    '/',
    name='Создать сообщество (канал)',
    description='Создаёт канал для текущего пользователя. '
                'Текущий пользователь автоматически становится владельцем и участником канала.',
    response_model=ReadChannel)
def create_channel(
        db: DBSessionDep,
        user: CurrentUserDep,
        creating_data: CreateChannel):
    new_channel = Channel.create(db, creating_data)
    channel_member = ChannelMember(
        channel_id=new_channel.id,
        user_id=user.id,
        permissions=Role.OWNER,
        is_owner=True
    )
    channel_member.save(db)
    return channel_member.channel


@router.put(
    '/{channel_id}/',
    name='Изменить сообщество (канал)',
    description='Изменяет канал. Если у пользователя нет прав на изменение канала, '
                'то возвращается HTTP 403 (Отказано в доступе).'
                'Если канала не существует, то возвращается HTTP 404 (Объект не найден).',
    response_model=ReadChannel)
def update_channel(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        channel_id: Annotated[int, Path(ge=1)],
        updating_data: UpdateChannel
):
    curr_member = get_current_channel_member(db, curr_user_info, channel_id)
    curr_member.has_permission_or_403(Permission.UPDATE_CHANNEL)
    channel = curr_member.channel
    channel.update(db, updating_data)
    return channel


@router.delete(
    '/{channel_id}/',
    name='Удалить сообщество (канал)',
    description='Удаляет (деактивирует) сообщество.'
)
def deactivate_channel(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        channel_id: Annotated[int, Path(ge=1)]
):
    curr_member = get_current_channel_member(db, curr_user_info, channel_id)
    curr_member.has_permission_or_403(Permission.DELETE_CHANNEL)
    channel = curr_member.channel
    channel.is_active = False
    channel.save(db)
    return channel


@router.patch(
    '/{channel_id}/recovery/',
    name='Восстановить сообщество (канал)',
    description='Восстановление канала доступно только владельцу канала, либо администратору сайта.',
    response_model=ReadChannel)
def recovery_channel(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        channel_id: Annotated[int, Path(ge=1)],
        recovery_data: RecoveryChannel
):
    curr_member = get_current_channel_member(db, curr_user_info, channel_id)
    if curr_member.user.is_staff or curr_member.is_owner:
        channel = curr_member.channel
        channel.update(db, recovery_data)
        return channel
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail='This operation is available only for staff user or channel owner.'
    )


@router.post(
    '/{channel_id}/subscribe/',
    name='Вступить в сообщество (канал)',
    description='Если сообщество публичное, то участник получает права MEMBER, иначе SUBSCRIBER.',
    tags=['Участники сообщества (channel members)'],
    response_model=ReadChannelMember)
def subscribe(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        channel_id: Annotated[int, Path(ge=1)],
        member_data: CreateChannelMember
):
    channel = get_or_404(Channel, db, id=channel_id)
    if channel.is_active:
        new_member = ChannelMember(
            user_id=curr_user_info.id,
            channel_id=channel.id,
            permissions=Role.MEMBER if channel.is_public else Role.CONFIRM_WAITER,
            notify_about_meeting=member_data.notify_about_meeting
        )
        new_member.save(db)
        return new_member
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail='Channel was deleted.'
    )


@router.get(
    '/{channel_id}/member/list/',
    name='Получить список участников сообщества (канала)',
    description='Возвращает список участников канала. Если у текущего пользователя нет права на просмотр участников, '
                'возвращает HTTP 403 (Отказано в доступе).',
    tags=['Участники сообщества (channel members)'],
    response_model=List[ReadChannelMember])
def members(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        channel_id: Annotated[int, Path(ge=1)],
        roles: Annotated[Set[Literal['OWNER', 'ADMIN', 'EDITOR', 'MEMBER', 'BLOCKED']], Query()]
):
    curr_member = get_current_channel_member(db, curr_user_info, channel_id)
    curr_member.has_permission_or_403(Permission.SEE_SUBSCRIBERS)
    role_codes = list(map(lambda r: getattr(Role, r), roles))
    if role_codes:
        return ChannelMember.filter(db, ChannelMember.channel_id == channel_id,
                                    ChannelMember.permissions.in_(role_codes),
                                    ChannelMember.date_of_join.isnot(None))
    else:
        ChannelMember.filter(db, ChannelMember.channel_id == channel_id,
                             ChannelMember.permissions.in_(role_codes),
                             ChannelMember.date_of_join.isnot(None))


@router.patch(
    '/{channel_id}/member/{member_id}/confirm/',
    name='Подтвердить участника сообщества (канала)',
    description='Дает права MEMBER подписчику канала.',
    tags=['Участники сообщества (channel members)'],
    response_model=ReadChannelMember)
def members(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        channel_id: Annotated[int, Path(ge=1)],
        member_id: Annotated[int, Path(description='This is target user id', ge=1)]
):
    curr_member = get_current_channel_member(db, curr_user_info, channel_id)
    curr_member.has_permission_or_403(Permission.GIVE_ACCESS)

    target_member = get_or_404(ChannelMember, db, channel_id=channel_id, user_id=member_id)
    target_member.permissions = Role.MEMBER
    target_member.save(db)
    return target_member


@router.patch(
    '/{channel_id}/member/{member_id}/role/',
    name='Изменить роль участника сообщества (канала)',
    description='Изменяет роль и соответственно права участника сообщества.',
    tags=['Участники сообщества (channel members)'],
    response_model=ReadChannelMember)
def edit_channel_member(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        channel_id: Annotated[int, Path(ge=1)],
        member_id: Annotated[int, Path(description='This is target user id', ge=1)],
        data: ChannelMemberRole
):
    curr_member = get_current_channel_member(db, curr_user_info, channel_id)
    curr_member.has_permission_or_403(Permission.GIVE_ACCESS)

    target_member = get_or_404(ChannelMember, db,
                               channel_id=channel_id, user_id=member_id)
    if target_member == curr_member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='You can not edit self permissions.')
    new_permissions = getattr(Role, data.role)
    if curr_member.channel.is_personal and data.role not in ['MEMBER', 'BLOCKED']:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f'You can only set MEMBER or BLOCKED role for personal channel member.'
        )
    curr_member.has_permission_or_403(new_permissions)
    target_member.permissions = new_permissions
    target_member.save(db)
    return target_member


@router.patch(
    '/{channel_id}/member/{member_id}/make-owner/',
    name='Передать права владельца сообщества (канала)',
    description='Доступно только для в владельца. Передает права владельца другому участнику. '
                'Для личного сообщества (канала) передача прав невозможна.',
    tags=['Участники сообщества (channel members)'],
    response_model=ReadChannelMember)
def give_owner_role(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        channel_id: Annotated[int, Path(ge=1)],
        member_id: Annotated[int, Path(description='This is target user id', ge=1)]
):
    curr_member = get_current_channel_member(db, curr_user_info, channel_id)
    target_member = get_or_404(ChannelMember, db,
                               channel_id=channel_id, user_id=member_id)
    if target_member == curr_member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='You can not edit self.')
    if not curr_member.is_owner:
        raise HTTPException(status_code=status.HTTP_403_BAD_REQUEST, detail='You are not owner.')
    if curr_member.channel.is_personal:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='You cant give owner role to other member, because it\'s personal channel')
    target_member.is_owner = True
    target_member.permissions = Role.OWNER
    curr_member.is_owner = False
    curr_member.permissions = Role.ADMIN
    db.add(curr_member)
    db.add(target_member)
    db.commit()
    db.refresh(target_member)
    return target_member


@router.delete(
    '/{channel_id}/subscribe/',
    name='Отписаться от сообщества (канала)',
    description='Если участник владелец права владельца передаются другому, '
                'если владелец единственный участник сообщества (канала) удаляется (деактивируется).'
                'Для владельцев личного сообщества (канала) операция не невозможна.',
    tags=['Участники сообщества (channel members)'])
def unsubscribe(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        channel_id: Annotated[int, Path(ge=1)]
):
    curr_member = get_or_404(ChannelMember, db,
                             user_id=curr_user_info.id, channel_id=channel_id)
    if curr_member is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'You are not member of channel (id={channel_id}).'
        )
    if curr_member.is_owner:
        if curr_member.channel.is_personal:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'You can not leave self channel ({curr_member.channel.id}) "{curr_member.channel.name}".'
            )
        else:
            delete_owner(db, curr_member)
    else:
        curr_member.delete(db)
