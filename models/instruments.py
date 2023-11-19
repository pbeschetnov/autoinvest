import datetime
from dataclasses import dataclass, field

from dataclasses_json import DataClassJsonMixin, dataclass_json, LetterCase, config
from dateutil.parser import parse

__all__ = [
    'Instrument',
]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Instrument(DataClassJsonMixin):
    ticker: str
    type: str
    working_schedule_id: int
    isin: str
    currency_code: str
    name: str
    short_name: str
    min_trade_quantity: float
    max_open_quantity: float
    added_on: datetime.datetime = field(metadata=config(decoder=parse))
