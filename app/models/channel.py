from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import mapped_column, relationship

from app.database.base import Base


class Channel(Base):
    __tablename__ = "channel"
    id = mapped_column("channel_id", Integer, primary_key=True)
    name = mapped_column(String(100), nullable=False)
    description = mapped_column(Text, nullable=True)
    members_cnt = mapped_column(Integer, nullable=False, default=0)
    rating = mapped_column(Float, nullable=True)
    is_personal = mapped_column(Boolean, nullable=False, default=False)
    is_public = mapped_column(Boolean, nullable=False, default=False)
    is_active = mapped_column(Boolean, nullable=False, default=True)

    members = relationship("ChannelMember", back_populates="channel")
    meetings = relationship("Meeting", back_populates="channel")
