from calendar import timegm
from datetime import datetime, timedelta, timezone

import pytz

from app import settings


def get_server_tzinfo():
    return pytz.timezone(settings.server.timezone)


def datetime_now() -> datetime:
    return datetime.now(get_server_tzinfo())


def convert_to_server_tz(_datetime: datetime) -> datetime:
    return _datetime.astimezone(get_server_tzinfo())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def add_delta_to_current_utc(
    days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0
) -> datetime:
    return datetime.now(timezone.utc) + timedelta(
        days, seconds, microseconds, milliseconds, minutes, hours, weeks
    )


def datetime_to_int(datetime: datetime) -> int:
    return timegm(datetime.utctimetuple())
