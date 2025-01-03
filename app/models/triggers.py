from sqlalchemy import Connection, event, insert, text, update
from sqlalchemy.orm import Mapper

from app.models import Channel, ChannelMember, Feedback, Meeting, User


@event.listens_for(User, "after_insert")
def create_personal_channel_trigger(mapper: Mapper[User], connection: Connection, target: User):
    stmt = (
        insert(Channel)
        .values(
            {
                "name": f"Канал пользователя {target.username}",
                "is_personal": True,
                "members_cnt": 1,
            }
        )
        .returning(Channel.id)
    )
    channel_id = connection.execute(stmt).scalar_one()
    stmt = insert(ChannelMember).values(
        {
            "user_id": target.id,
            "channel_id": channel_id,
            "permissions": 32767,
            "is_owner": True,
        }
    )
    connection.execute(stmt)


@event.listens_for(Feedback, "after_insert")
@event.listens_for(Feedback, "after_update")
@event.listens_for(Feedback, "after_delete")
def update_meeting_rating_trigger(mapper: Mapper[Feedback], connection: Connection, target: Feedback):
    avg_stmt = text("select avg(rate) from feedback where meeting_id = :meeting_id").params(
        meeting_id=target.meeting_id
    )
    avg = connection.execute(avg_stmt).scalar_one()
    stmt = update(Meeting).where(Meeting.id == target.meeting_id).values(rating=avg)
    connection.execute(stmt)


@event.listens_for(ChannelMember, "after_insert")
def increment_channel_members_cnt_trigger(
    mapper: Mapper[ChannelMember], connection: Connection, target: ChannelMember
):
    stmt = text(
        "update channel "
        "set members_cnt = (select members_cnt from channel where channel_id = :channel_id) + 1 "
        "where channel.channel_id = :channel_id"
    )
    connection.execute(stmt.params(channel_id=target.channel_id))


@event.listens_for(ChannelMember, "after_delete")
def decrement_channel_members_cnt_trigger(
    mapper: Mapper[ChannelMember], connection: Connection, target: ChannelMember
):
    stmt = text(
        "update channel "
        "set members_cnt = (select members_cnt from channel where channel_id = :channel_id) - 1 "
        "where channel.channel_id = :channel_id"
    )
    connection.execute(stmt.params(channel_id=target.channel_id))
