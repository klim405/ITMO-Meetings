import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, update, Uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app import settings
from app.database import Base
from app.utils.time import add_delta_to_current_utc, utc_now


def _expires_at() -> datetime:
    return add_delta_to_current_utc(minutes=settings.auth.refresh_token_lifetime_in_min)


class RefreshToken(Base):
    __tablename__ = "refresh_token"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    issues_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_expires_at)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    is_staff: Mapped[bool] = mapped_column(nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("person.user_id"), nullable=False)

    @classmethod
    async def revoke_all(cls, db_session: AsyncSession, user_id: int) -> None:
        stmt = update(cls).where(cls.user_id == user_id).values(is_active=False)
        await db_session.execute(stmt)
        await db_session.commit()
