import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import List

from dataclasses_json import DataClassJsonMixin, dataclass_json, LetterCase, config
from dateutil.parser import parse

__all__ = [
    'DividendCashAction',
    'Result',
    'Instrument',
    'Settings',
    'Pie',
]


class DividendCashAction(Enum):
    REINVEST = "REINVEST"
    PAY_CASH = "PAY_CASH"


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Result(DataClassJsonMixin):
    invested_value: float
    value: float
    result: float
    result_coef: float


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Instrument(DataClassJsonMixin):
    ticker: str
    result: Result
    expected_share: float
    current_share: float
    owned_quantity: float


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Settings(DataClassJsonMixin):
    id: int
    name: str
    creation_date: datetime.datetime = field(metadata=config(decoder=parse))
    dividend_cash_action: DividendCashAction


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Pie(DataClassJsonMixin):
    instruments: List[Instrument]
    settings: Settings
