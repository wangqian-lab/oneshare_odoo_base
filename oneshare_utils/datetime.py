# -*- coding: utf-8 -*-
import pytz
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATE_LENGTH, \
    DEFAULT_SERVER_TIME_FORMAT
from typing import Union
from datetime import datetime, date, timedelta
import os

RFC3339_SERVER_DATETIME_FORMAT = "%sT%s" % (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_TIME_FORMAT)
DEFAULT_SERVER_DATETIME_FORMAT_TZ = f'{DEFAULT_SERVER_DATETIME_FORMAT}%z'
RFC3339_SERVER_DATETIME_FORMAT_TZ = f'{RFC3339_SERVER_DATETIME_FORMAT}%z'
ENV_DEFAULT_TIMEZONE = os.getenv('ENV_DEFAULT_TIMEZONE', 'Asia/Shanghai')

DEFAULT_TZ = pytz.timezone(ENV_DEFAULT_TIMEZONE)

DATETIME_LENGTH = len(datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT))


def local_datetime_from_str(ss='', tz_local=DEFAULT_TZ) -> datetime:
    ll = len(ss)
    if ll < DATE_LENGTH:
        d = datetime.now()
    elif len(ss) == DATE_LENGTH:
        d = datetime.strptime(ss, DEFAULT_SERVER_DATE_FORMAT)
    elif len(ss) == DATETIME_LENGTH:
        d = datetime.strptime(ss, DEFAULT_SERVER_DATETIME_FORMAT)
    else:
        try:
            # 尝试rfc3339格式
            d = datetime.strptime(ss, RFC3339_SERVER_DATETIME_FORMAT_TZ)  # 包含时区信息
        except Exception as e:
            d = datetime.strptime(ss, DEFAULT_SERVER_DATETIME_FORMAT_TZ)  # 包含时区信息
        return d
    return tz_local.localize(d)


def local_datetime_to_utc(dd: Union[datetime, str], tz_local=DEFAULT_TZ) -> datetime:
    if isinstance(dd, str):
        dd = local_datetime_from_str(dd)
    return tz_local.normalize(dd).astimezone(pytz.utc)


def local_date_from_str(ss: str = '', tz_local=DEFAULT_TZ) -> datetime:
    if len(ss) < DATE_LENGTH:
        d = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        d = datetime.strptime(ss, DEFAULT_SERVER_DATE_FORMAT)
    return tz_local.localize(d)


def now(tz_local=DEFAULT_TZ) -> str:
    now_utc = datetime.now()
    if isinstance(now_utc, str):
        now_utc = datetime.now().replace(microsecond=0, tzinfo=pytz.utc)
    return now_utc.astimezone(tz_local).strftime(DEFAULT_SERVER_DATETIME_FORMAT)


def tomorrow(tz_local=DEFAULT_TZ) -> str:
    tomorrow_utc = datetime.today() + timedelta(days=1)
    return tomorrow_utc.astimezone(tz_local).strftime(DEFAULT_SERVER_DATE_FORMAT)


def months(d, prev=False, tz_local=DEFAULT_TZ) -> str:
    delta = int(d * 4)
    if prev:
        tomorrow_utc = datetime.today() - timedelta(weeks=delta)
    else:
        tomorrow_utc = datetime.today() + timedelta(weeks=delta)
    return tomorrow_utc.astimezone(tz_local).strftime(DEFAULT_SERVER_DATE_FORMAT)


def today(tz_local=DEFAULT_TZ) -> str:
    today_utc = datetime.today()
    if isinstance(today_utc, str):
        today_utc = datetime.today().replace(tzinfo=pytz.utc)
    return today_utc.astimezone(tz_local).strftime(DEFAULT_SERVER_DATE_FORMAT)
