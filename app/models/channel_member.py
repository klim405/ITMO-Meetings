from fastapi import HTTPException, status
from sqlalchemy import Boolean, DateTime, ForeignKey, ForeignKeyConstraint, Integer
from sqlalchemy.orm import mapped_column, relationship

from app.database.base import Base
from app.utils.time import datetime_now


class Permission:
    """Права ChannelMember на внесение изменений в канале"""

    # Channel
    DELETE_CHANNEL = 0b1000000000000000
    UPDATE_CHANNEL = 0b0100000000000000
    # RESERVED     = 0b0010000000000000
    # RESERVED     = 0b0001000000000000

    # Management
    GIVE_ACCESS = 0b0000100000000000
    # RESERVED    = 0b0000010000000000
    # RESERVED    = 0b0000001000000000
    SEE_USER_INFO = 0b0000000100000000

    # Meeting CRUD
    CREATE_MEETING = 0b0000000010000000
    UPDATE_MEETING = 0b0000000001000000
    DELETE_MEETING = 0b0000000000100000
    SEE_MEETINGS = 0b0000000000010000

    # General
    SEE_SUBSCRIBERS = 0b0000000000001000
    # RESERVED           = 0b0000000000000100
    SEE_MEETINGS_MEMBERS = 0b0000000000000010
    JOIN_TO_MEETING = 0b0000000000000001

    NONE = 0


class Role:
    """Роли подписчиков канала"""

    OWNER = (
        Permission.DELETE_CHANNEL
        | Permission.UPDATE_CHANNEL
        | Permission.GIVE_ACCESS
        | Permission.SEE_USER_INFO
        | Permission.CREATE_MEETING
        | Permission.UPDATE_MEETING
        | Permission.UPDATE_MEETING
        | Permission.SEE_MEETINGS
        | Permission.SEE_SUBSCRIBERS
        | Permission.SEE_MEETINGS_MEMBERS
        | Permission.JOIN_TO_MEETING
    )
    ADMIN = (
        Permission.UPDATE_CHANNEL
        | Permission.GIVE_ACCESS
        | Permission.SEE_USER_INFO
        | Permission.CREATE_MEETING
        | Permission.UPDATE_MEETING
        | Permission.UPDATE_MEETING
        | Permission.SEE_MEETINGS
        | Permission.SEE_SUBSCRIBERS
        | Permission.SEE_MEETINGS_MEMBERS
        | Permission.JOIN_TO_MEETING
    )
    EDITOR = (
        Permission.SEE_USER_INFO
        | Permission.CREATE_MEETING
        | Permission.UPDATE_MEETING
        | Permission.UPDATE_MEETING
        | Permission.SEE_MEETINGS
        | Permission.SEE_SUBSCRIBERS
        | Permission.SEE_MEETINGS_MEMBERS
        | Permission.JOIN_TO_MEETING
    )
    MEMBER = (
        Permission.SEE_MEETINGS
        | Permission.SEE_SUBSCRIBERS
        | Permission.SEE_MEETINGS_MEMBERS
        | Permission.JOIN_TO_MEETING
    )
    GUEST = (
        Permission.SEE_MEETINGS
        | Permission.SEE_SUBSCRIBERS
        | Permission.SEE_MEETINGS_MEMBERS
        | Permission.JOIN_TO_MEETING
    )
    ANONYMOUS = Permission.NONE
    CONFIRM_WAITER = Permission.NONE
    BLOCKED = Permission.SEE_SUBSCRIBERS | Permission.SEE_MEETINGS


class ChannelMember(Base):
    __tablename__ = "channel_member"
    __table_args__ = (
        ForeignKeyConstraint(
            ["channel_id", "user_id"], ["channel_member.channel_id", "channel_member.user_id"]
        ),
    )

    channel_id = mapped_column("channel_id", Integer, ForeignKey("channel.channel_id"), primary_key=True)
    user_id = mapped_column("user_id", Integer, ForeignKey("person.user_id"), primary_key=True)

    date_of_join = mapped_column(DateTime(timezone=True), default=datetime_now())
    permissions = mapped_column(Integer, nullable=False, default=Permission.NONE)
    is_owner = mapped_column(Boolean, nullable=False, default=False)
    notify_about_meeting = mapped_column(Boolean, nullable=False, default=False)

    channel = relationship("Channel", back_populates="members", lazy="subquery")
    user = relationship("User", back_populates="channel_members", lazy="subquery")

    def has_permission_or_403(self, permission: int) -> None:
        if self.permissions & permission != permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You has not permission {bin(permission)}",
            )
