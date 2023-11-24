from datetime import datetime

from pydantic import BaseModel


class ChannelMember(BaseModel):
    notify_about_meeting: bool = False


class CreateChannelMember(ChannelMember):
    pass


class ChannelMemberPermissions(BaseModel):
    permissions: int


class ReadChannelMember(ChannelMember):
    user_id: int
    channel_id: int

    permissions: int
    is_owner: bool

    date_of_join: datetime
