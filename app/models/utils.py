from sqlalchemy.ext.asyncio import AsyncSession

from app.models.channel_member import ChannelMember, Role
from app.models.user import User


async def delete_owner(db_session: AsyncSession, old_owner: ChannelMember):
    channel = old_owner.channel
    members = channel.members
    if len(members) > 1:  # Если у кана есть другие участники, то права владельца передаются
        members: list = members.copy()
        members.remove(old_owner)
        new_owner = max(members, key=lambda cm: cm.permissions)
        new_owner.permissions = Role.OWNER
        new_owner.is_owner = True
        db_session.add(new_owner)
        await db_session.delete(old_owner)
    else:  # Иначе канал деактивируется
        channel.is_active = False
        db_session.add(channel)
    await db_session.commit()


async def deactivate_user(db_session: AsyncSession, user: User):
    # Находим информацию о сообществах, где владелец деактивируемый пользователь.
    owner_members = await ChannelMember.filter(
        db_session, (ChannelMember.user_id == user.id) & (ChannelMember.is_owner == True)  # noqa: E712
    )
    for owner_member in owner_members:
        channel = owner_member.channel
        if channel.is_personal:  # Личные каналы деактивируем
            channel.is_active = False
            db_session.add(channel)
        else:
            members = channel.members.copy()
            if len(members) > 1:  # Если у кана есть другие участники, то права владельца передаются
                members: list = members.copy()
                members.remove(owner_member)
                new_owner = max(members, key=lambda cm: cm.permissions)
                new_owner.permissions = Role.OWNER
                new_owner.is_owner = True
                owner_member.is_owner = False
                owner_member.permissions = Role.ADMIN
                db_session.add(new_owner)
                db_session.add(owner_member)
            else:  # Иначе канал деактивируется
                channel.is_active = False
                db_session.add(channel)
    user.is_active = False
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
