from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field

from app.schemas.validators import date_time_to_server_tz, datetime_more_then_now


class MeetingBase(BaseModel):
    title: str = Field(min_length=3, max_length=256, examples=["My super party"])
    description: str | None = Field(
        default=None, examples=["If you will come, you will have unreal emotions."]
    )
    start_datetime: Annotated[
        datetime,
        AfterValidator(date_time_to_server_tz),
        AfterValidator(datetime_more_then_now(hours=1)),
    ]
    duration_in_minutes: int | None = Field(ge=15, le=24 * 60, examples=[15])
    address: str = Field(min_length=3, max_length=512)
    capacity: int = Field(ge=4, examples=[4])
    price: int = Field(default=0, ge=0)
    minimum_age: int = Field(default=0, ge=0)
    maximum_age: int = Field(default=150, ge=0)
    only_for_itmo_students: bool = False
    only_for_russians: bool = False


class CreateMeeting(MeetingBase):
    channel_id: int = Field(ge=1)


class UpdateMeeting(MeetingBase):
    pass


class ReadMeeting(MeetingBase):
    id: int
    channel_id: int
    start_datetime: datetime
    rating: float | None = None
