import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import List

from dataclasses_json import DataClassJsonMixin
from dataclasses_json import dataclass_json, LetterCase, config
from dateutil.parser import parse

__all__ = [
    'EventType',
    'TimeEvent',
    'WorkingSchedule',
    'Exchange',
]


class EventType(str, Enum):
    OPEN = 'OPEN'
    CLOSE = 'CLOSE'
    PRE_MARKET_OPEN = 'PRE_MARKET_OPEN'
    AFTER_HOURS_OPEN = 'AFTER_HOURS_OPEN'
    AFTER_HOURS_CLOSE = 'AFTER_HOURS_CLOSE'


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class TimeEvent(DataClassJsonMixin):
    date: datetime.datetime = field(metadata=config(decoder=parse))
    type: EventType


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class WorkingSchedule(DataClassJsonMixin):
    id: int
    time_events: List[TimeEvent]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Exchange(DataClassJsonMixin):
    id: int
    name: str
    working_schedules: List[WorkingSchedule]
