from datetime import date, datetime, timedelta

from app.utils.time import convert_to_server_tz, datetime_now


def date_time_to_server_tz(v: datetime):
    return convert_to_server_tz(v)


def datetime_more_then_now(
    *,
    days: float = 0,
    seconds: float = 0,
    microseconds: float = 0,
    milliseconds: float = 0,
    minutes: float = 0,
    hours: float = 0,
    weeks: float = 0
):
    def validator(v: datetime):
        delta = timedelta(days, seconds, microseconds, milliseconds, minutes, hours, weeks)
        if v < datetime_now() + delta:
            raise ValueError("Datetime is less than now")
        return v

    return validator


def datetime_less_then_now(
    *,
    days: float = 0,
    seconds: float = 0,
    microseconds: float = 0,
    milliseconds: float = 0,
    minutes: float = 0,
    hours: float = 0,
    weeks: float = 0
):
    def validator(v: datetime):
        delta = timedelta(days, seconds, microseconds, milliseconds, minutes, hours, weeks)
        if v > datetime_now() - delta:
            raise ValueError("Datetime is more than now")
        return v

    return validator


def age_validator(age: int):
    def validator(v: date):
        today = date.today()
        if today.year - v.year < age or (
            today.year - v.year == age
            and (today.month < v.month or (today.month == v.month and today.day < v.day))
        ):
            raise ValueError("Age is small")
        return v

    return validator
