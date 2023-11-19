import datetime
import functools
import json
import logging
from dataclasses import dataclass
from typing import Any, Optional, List, Tuple

from config import *

__all__ = [
    'setup_logging',
    'now',
    'cached_method',
    'build_state',
]


def setup_logging(level=logging.INFO, filename='autoinvest.log'):
    logging.basicConfig(
        level=level,
        format='[%(name)s\t%(levelname)s\t%(asctime)s]\t%(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(filename),
        ],
    )


def now():
    return datetime.datetime.now(tz=TIMEZONE)


@dataclass
class CacheObject:
    value: Any
    cached_at: datetime.datetime


def cached_method(ttl: Optional[datetime.timedelta] = None):
    def wrapper(func):
        @functools.wraps(func)
        def wrapped(self, *args, **kwargs):
            key = json.dumps({
                'func': func.__name__,
                'args': [repr(x) for x in args],
                'kwargs': {k: repr(v) for k, v in kwargs.items()},
            }, sort_keys=True)
            if not hasattr(self, '__method_cache'):
                self.__method_cache = {}
            if key not in self.__method_cache or (ttl and now() - self.__method_cache[key].cached_at > ttl):
                value = func(self, *args, **kwargs)
                self.__method_cache[key] = CacheObject(value, now())
            return self.__method_cache[key].value

        return wrapped

    return wrapper


def build_state(pie_composition: List[Tuple[str, float]]) -> List[Tuple[str, str]]:
    return sorted([
        ('mode', MODE.name),
        ('pie_name', AUTOINVEST_PIE),
        ('pie_composition', str(pie_composition)),
        ('master_currency', MASTER_CURRENCY),
        ('weekly_amount', str(WEEKLY_AMOUNT)),
        ('investment_period', str(INVESTMENT_PERIOD))
    ], key=lambda x: x[0])
