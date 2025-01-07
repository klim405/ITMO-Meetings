from datetime import datetime

import pytz

from app import settings


def get_server_tzinfo():
    return pytz.timezone(settings.server.timezone)


def datetime_now() -> datetime:
    return datetime.now(get_server_tzinfo())


def convert_to_server_tz(_datetime: datetime) -> datetime:
    return _datetime.astimezone(get_server_tzinfo())
