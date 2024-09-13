from app.schemas.channel import ReadChannel
from app.schemas.channel_member import ReadChannelMember


class ChannelMemberWithChannel(ReadChannelMember):
    channel: ReadChannel
