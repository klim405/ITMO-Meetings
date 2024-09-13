from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ChannelMember(BaseModel):
    notify_about_meeting: bool = False


class CreateChannelMember(ChannelMember):
    pass


class ChannelMemberRole(BaseModel):
    permissions: Literal['OWNER', 'ADMIN', 'EDITOR', 'MEMBER', 'BLOCKED']


class ReadChannelMember(ChannelMember):
    user_id: int
    channel_id: int

    permissions: int
    is_owner: bool

    date_of_join: datetime
