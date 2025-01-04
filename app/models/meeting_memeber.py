from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import mapped_column, relationship

from app.database.base import Base
from app.utils.time import datetime_now


class MeetingMember(Base):
    __tablename__ = "meeting_member"
    __table_args__ = {"extend_existing": True}
    user_id = mapped_column(Integer, ForeignKey("person.user_id"), primary_key=True)
    meeting_id = mapped_column(Integer, ForeignKey("meeting.meeting_id"), primary_key=True)
    date_of_join = mapped_column(DateTime(timezone=True), nullable=False, default=datetime_now)

    user = relationship("User")
    meeting = relationship("Meeting")
