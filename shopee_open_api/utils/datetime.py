from datetime import datetime


def datetime_string_from_unix(unix: float) -> str:
    return datetime_to_str(datetime_from_unix(unix))


def datetime_from_unix(unix: float) -> datetime:
    return datetime.utcfromtimestamp(unix)


def datetime_to_str(datetime: datetime) -> str:
    return datetime.strftime("%Y-%m-%d %H:%M:%S")
