import enum
from functools import cache
from typing import Optional, Set

from sqlalchemy import Boolean, Date
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.database import Base
from app.models.secondary_tables import favorite_category, meeting_member


class Gender(enum.Enum):
    male = "male"
    female = "female"


class Confidentiality:
    HIDE_AVATAR = 0b100000000
    HIDE_USERNAME = 0b010000000
    HIDE_PATRONYMIC = 0b001000000
    HIDE_SURNAME = 0b000100000
    HIDE_BIRTHDATE = 0b000010000
    HIDE_TELEPHONE = 0b000001000
    HIDE_EMAIL = 0b000000100
    HIDE_CHANNELS = 0b000000010
    HIDE_CATEGORIES = 0b000000001


ALL_CONFIDENTIALITY = 0b111111111
DEFAULT_CONFIDENTIALITY = (
    Confidentiality.HIDE_PATRONYMIC | Confidentiality.HIDE_TELEPHONE | Confidentiality.HIDE_EMAIL
)


class User(Base):
    __tablename__ = "person"
    id = mapped_column("user_id", Integer, primary_key=True)
    referrer_id = mapped_column(Integer, ForeignKey("person.user_id"), nullable=True)
    referer = relationship("User", remote_side=[id])

    # credentials
    username = mapped_column(String(20), unique=True, nullable=True)
    telephone = mapped_column(String(64), unique=True, nullable=False)
    email = mapped_column(String(320), unique=True, nullable=False)
    password_hash = mapped_column(String(182), nullable=False)

    # personal info
    firstname = mapped_column(String(20), nullable=False)
    patronymic = mapped_column(String(20), nullable=True)
    surname = mapped_column(String(20), nullable=False)
    other_names = mapped_column(String(256), nullable=True)
    gender = mapped_column(SQLEnum(Gender), nullable=False)
    date_of_birth = mapped_column(Date, nullable=False)

    # security
    confidentiality = mapped_column(Integer, nullable=False, default=DEFAULT_CONFIDENTIALITY)
    is_staff = mapped_column(Boolean, nullable=False, default=False)
    is_active = mapped_column(Boolean, nullable=False, default=True)

    favorites_categories = relationship("Category", secondary=favorite_category)
    channel_members = relationship("ChannelMember", back_populates="user")
    meetings = relationship("Meeting", secondary=meeting_member, back_populates="members")
    feedbacks = relationship("Feedback", back_populates="user")

    @property
    def password(self):
        raise AttributeError("password is not readable attribute.")

    @password.setter
    def password(self, plain_password):
        self.password_hash = generate_password_hash(
            plain_password, method="pbkdf2:sha512:600000", salt_length=32
        )

    def verify_password(self, plain_password):
        return check_password_hash(self.password_hash, plain_password)

    @staticmethod
    @cache
    def _get_private_field_names(confidentiality: int) -> set:
        private_fields = set()
        # if confidentiality & Confidentiality.HIDE_AVATAR:
        #     private_fields.append('avatar')
        if confidentiality & Confidentiality.HIDE_USERNAME:
            private_fields.add("username")
        if confidentiality & Confidentiality.HIDE_PATRONYMIC:
            private_fields.add("patronymic")
        if confidentiality & Confidentiality.HIDE_SURNAME:
            private_fields.add("surname")
        if confidentiality & Confidentiality.HIDE_BIRTHDATE:
            private_fields.add("date_of_birth")
        if confidentiality & Confidentiality.HIDE_TELEPHONE:
            private_fields.add("telephone")
        if confidentiality & Confidentiality.HIDE_EMAIL:
            private_fields.add("email")
        if confidentiality & Confidentiality.HIDE_CHANNELS:
            private_fields.add("channels")
        if confidentiality & Confidentiality.HIDE_CATEGORIES:
            private_fields.add("favorites_categories")
        return private_fields

    def get_private_field_names(self) -> Set[str]:
        return self._get_private_field_names(self.confidentiality)

    @classmethod
    async def get_by_login(cls, db_session: AsyncSession, login: str) -> Optional["User"]:
        return await cls.get_first_by_filter(
            db_session, (cls.username == login) | (cls.telephone == login) | (cls.email == login)
        )
