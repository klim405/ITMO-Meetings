from sqlalchemy.orm import Session

from app.auth.deps import UserInfo
from app.database.utils import get_or_404
from app.models import Channel, ChannelMember, User
from app.models.channel_member import Role


def get_current_channel_member(db_session: Session, curr_user: UserInfo, channel_id: int) -> ChannelMember:
    member = ChannelMember.get(db_session, user_id=curr_user.id, channel_id=channel_id)
    if member is not None:
        return member
    channel = get_or_404(Channel, db_session, id=channel_id)
    return ChannelMember(
        user_id=curr_user.id,
        channel_id=channel_id,
        user=User.get(db_session, id=curr_user.id),
        channel=channel,
        permissions=Role.GUEST if channel.is_public else Role.ANONYMOUS,
    )
