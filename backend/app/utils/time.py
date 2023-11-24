import datetime

import pytz

from app.settings import settings


def datetime_now():
    return datetime.datetime.now(pytz.timezone(settings.SERVER_TIMEZONE))
