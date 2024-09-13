from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column, relationship

from app.database.base import Base
from app.models.secondary_tables import meeting_category


class Category(Base):
    __tablename__ = 'category'
    id = mapped_column('category_id', Integer, primary_key=True, index=True)
    name = mapped_column(String(20), nullable=False)

    meetings = relationship('Meeting', secondary=meeting_category,
                            back_populates='categories')
