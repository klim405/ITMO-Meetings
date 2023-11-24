from fastapi import HTTPException, status
from sqlalchemy import ForeignKey, DateTime, Integer, Boolean, ForeignKeyConstraint
from sqlalchemy.orm import mapped_column, relationship

from app.database.base import Base
from app.utils.time import datetime_now


class Permission:
    """ Права ChannelMember на внесение изменений в канале """
    DELETE_CHANNEL = 0b01000000
    UPDATE_CHANNEL = 0b00100000
    GIVE_ACCESS = 0b00010000
    UPDATE_MEETING = 0b00001000
    SEE_MEMBERS = 0b00000100
    RESERVED = 0b00000010
    JOIN_TO_MEETING = 0b00000001
    NONE = 0b00000000


class Role:
    """ Роли подписчиков канала """
    OWNER = (Permission.UPDATE_CHANNEL | Permission.DELETE_CHANNEL | Permission.GIVE_ACCESS
             | Permission.UPDATE_MEETING | Permission.SEE_MEMBERS | Permission.JOIN_TO_MEETING)
    ADMIN = (Permission.UPDATE_CHANNEL | Permission.GIVE_ACCESS | Permission.UPDATE_MEETING
             | Permission.SEE_MEMBERS | Permission.JOIN_TO_MEETING)
    EDITOR = Permission.UPDATE_MEETING | Permission.SEE_MEMBERS | Permission.JOIN_TO_MEETING
    MEMBER = Permission.SEE_MEMBERS | Permission.JOIN_TO_MEETING
    SUBSCRIBER = Permission.NONE
    GUEST = Permission.NONE
    BLOCKED = Permission.SEE_MEMBERS


class ChannelMember(Base):
    __tablename__ = 'channel_member'
    __table_args__ = (
        ForeignKeyConstraint(
            ['channel_id', 'user_id'],
            ['channel_member.channel_id', 'channel_member.user_id']
        ),
    )

    channel_id = mapped_column('channel_id', Integer, ForeignKey('channel.channel_id'), primary_key=True)
    user_id = mapped_column('user_id', Integer, ForeignKey('person.user_id'), primary_key=True)

    date_of_join = mapped_column(DateTime(timezone=True), default=datetime_now())
    permissions = mapped_column(Integer, nullable=False, default=Permission.NONE)
    is_owner = mapped_column(Boolean, nullable=False, default=False)
    notify_about_meeting = mapped_column(Boolean, nullable=False, default=False)

    channel = relationship('Channel', back_populates='members', lazy='subquery')
    user = relationship('User', back_populates='channel_members', lazy='subquery')

    def has_permission_or_403(self, permission: int) -> None:
        if self.permissions & permission != permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'You has not permission {bin(permission)}'
            )
