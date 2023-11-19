import datetime
from dataclasses import dataclass, field, replace

from dataclasses_json import dataclass_json, LetterCase, config, DataClassJsonMixin
from dateutil.parser import parse

__all__ = [
    'Order',
    'ScheduledOrder',
]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Order(DataClassJsonMixin):
    ticker: str = field(metadata=config(field_name="code"))
    amount: float = field(metadata=config(field_name="value"))
    currency: str = field(metadata=config(field_name="currencyCode"))
    created_at: datetime.datetime = field(metadata=config(field_name="created", decoder=parse))


@dataclass
class ScheduledOrder:
    ticker: str
    amount: float  # in master currency
    currency: str  # ticker currency
    execute_at: datetime.datetime

    def __str__(self):
        execute_at_str = self.execute_at.replace(microsecond=0).astimezone(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
        return repr(replace(self, execute_at=execute_at_str))
