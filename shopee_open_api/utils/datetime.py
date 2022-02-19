import frappe
import pytz

from datetime import datetime, timezone


def datetime_string_from_unix(unix: float) -> str:
    datetime_string = datetime_to_str(datetime_from_unix(unix))
    return datetime_string


def datetime_from_unix(unix: float) -> datetime:
    timezone_name = frappe.db.get_default("time_zone")
    timezone_obj = pytz.timezone(timezone_name)
    utc_datetime = datetime.utcfromtimestamp(unix)
    local_datetime = utc_datetime.replace(tzinfo=timezone.utc).astimezone(timezone_obj)
    return local_datetime


def datetime_to_str(datetime: datetime) -> str:
    return datetime.strftime("%Y-%m-%d %H:%M:%S")
