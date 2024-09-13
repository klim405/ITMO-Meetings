from sqlalchemy import Integer, ForeignKey, String, Text, DateTime, CheckConstraint, Boolean, Float
from sqlalchemy.orm import mapped_column, relationship

from app.database.base import Base
from app.models.secondary_tables import meeting_member, meeting_category


class Meeting(Base):
    __tablename__ = 'meeting'
    id = mapped_column('meeting_id', Integer, primary_key=True)
    channel_id = mapped_column(Integer, ForeignKey('channel.channel_id'), nullable=False)
    title = mapped_column(String(256), nullable=False)
    description = mapped_column(Text)
    start_datetime = mapped_column(DateTime(timezone=True), nullable=False)
    duration_in_minutes = mapped_column(Integer, default=None)
    address = mapped_column(String(512), nullable=False)
    capacity = mapped_column(Integer, CheckConstraint('capacity > 0'), default=4)
    price = mapped_column(Integer, CheckConstraint('price >= 0'), default=0)
    minimum_age = mapped_column(Integer, CheckConstraint('minimum_age >= 0'), default=0)
    maximum_age = mapped_column(Integer, CheckConstraint('maximum_age >= 0'), default=150)
    only_for_itmo_students = mapped_column(Boolean, nullable=False, default=False)
    only_for_russians = mapped_column(Boolean, nullable=False, default=False)
    rating = mapped_column(Float, default=None)

    channel = relationship('Channel', back_populates='meetings')
    members = relationship('User', secondary=meeting_member, back_populates='meetings')
    categories = relationship('Category', secondary=meeting_category,
                              back_populates='meetings')
    feedbacks = relationship('Feedback', back_populates='meeting')
