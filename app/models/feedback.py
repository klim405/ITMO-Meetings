from sqlalchemy import CheckConstraint, ForeignKey, Integer
from sqlalchemy.orm import mapped_column, relationship

from app.database.base import Base


class Feedback(Base):
    __tablename__ = "feedback"
    user_id = mapped_column(Integer, ForeignKey("person.user_id"), primary_key=True)
    meeting_id = mapped_column(Integer, ForeignKey("meeting.meeting_id"), primary_key=True)
    rate = mapped_column(Integer, CheckConstraint("rate >= 0 and rate <= 5"), nullable=False)

    user = relationship("User", back_populates="feedbacks")
    meeting = relationship("Meeting", back_populates="feedbacks")
