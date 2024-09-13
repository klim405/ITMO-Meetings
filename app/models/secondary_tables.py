from sqlalchemy import Column, ForeignKey, Table

from app.database import Base

meeting_category = Table(
    "meeting_category",
    Base.metadata,
    Column("meeting_id", ForeignKey("meeting.meeting_id"), primary_key=True),
    Column("category_id", ForeignKey("category.category_id"), primary_key=True),
)

meeting_member = Table(
    "meeting_member",
    Base.metadata,
    Column("meeting_id", ForeignKey("meeting.meeting_id"), primary_key=True),
    Column("user_id", ForeignKey("person.user_id"), primary_key=True),
)

favorite_category = Table(
    "favorite_category",
    Base.metadata,
    Column("user_id", ForeignKey("person.user_id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("category.category_id", ondelete="CASCADE"), primary_key=True),
)
