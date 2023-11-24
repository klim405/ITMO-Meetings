from typing import Annotated

from fastapi import APIRouter, Depends, Path, HTTPException, status

from app.api.deps import get_current_channel_member
from app.auth.deps import get_current_user, CurrentUserDep
from app.database.deps import DBSessionDep
from app.database.utils import get_or_404
from app.models import Channel, ChannelMember
from app.models.channel_member import Role, Permission
from app.models.utils import delete_owner
from app.schemas.channel import ReadChannel, CreateChannel, UpdateChannel, RecoveryChannel
from app.schemas.channel_member import ReadChannelMember, CreateChannelMember, ChannelMemberPermissions

router = APIRouter()


@router.get('/{channel_id}/', response_model=ReadChannel,
            dependencies=[Depends(get_current_user)])
def get_channel(db: DBSessionDep, channel_id: Annotated[int, Path(ge=1)]):
    return get_or_404(Channel, db, id=channel_id)


@router.post('/', response_model=ReadChannel)
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


@router.put('/{channel_id}/', response_model=ReadChannel)
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


@router.delete('/{channel_id}/')
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


@router.patch('/{channel_id}/recovery/',
              description='Reactivate channel, this operation is available only for owner or staff user.',
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


@router.post('/{channel_id}/subscribe/', response_model=ReadChannelMember)
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
            permissions=Role.MEMBER if channel.is_public else Role.SUBSCRIBER,
            notify_about_meeting=member_data.notify_about_meeting
        )
        new_member.save(db)
        return new_member
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail='Channel was deleted.'
    )


@router.patch('/{channel_id}/member/{member_id}/permissions/', response_model=ReadChannelMember)
def edit_channel_member(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        channel_id: Annotated[int, Path(ge=1)],
        member_id: Annotated[int, Path(ge=1)],
        data: ChannelMemberPermissions
):
    curr_member = get_current_channel_member(db, curr_user_info, channel_id)
    target_member = get_or_404(ChannelMember, db,
                               channel_id=channel_id, user_id=member_id)
    if target_member == curr_member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='You can not edit self permissions.')
    curr_member.has_permission_or_403(Permission.GIVE_ACCESS)
    curr_member.has_permission_or_403(data.permissions)
    target_member.permissions = data.permissions
    target_member.save(db)
    return target_member


@router.patch('/{channel_id}/member/{member_id}/make-owner/', response_model=ReadChannelMember)
def edit_channel_member(
        db: DBSessionDep,
        curr_user_info: CurrentUserDep,
        channel_id: Annotated[int, Path(ge=1)],
        member_id: Annotated[int, Path(ge=1)]
):
    curr_member = get_current_channel_member(db, curr_user_info, channel_id)
    target_member = get_or_404(ChannelMember, db,
                               channel_id=channel_id, user_id=member_id)
    if target_member == curr_member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='You can not edit self.')
    if not curr_member.is_owner:
        raise HTTPException(status_code=status.HTTP_403_BAD_REQUEST, detail='You are not owner.')
    target_member.is_owner = True
    target_member.permissions = Role.OWNER
    curr_member.is_owner = False
    curr_member.permissions = Role.ADMIN
    db.add(curr_member)
    db.add(target_member)
    db.commit()
    db.refresh(target_member)
    return target_member


@router.delete('/{channel_id}/subscribe/')
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
