import datetime
import random
from dataclasses import dataclass
from typing import List

import db
from api_client import T212ApiClient
from models.exchanges import EventType
from models.exchanges import WorkingSchedule
from models.orders import ScheduledOrder
from models.pies import Pie
from utils import *

__all__ = [
    'Instrument',
    'collect_instruments',
    'schedule_orders',
    'validate_orders',
]


@dataclass
class Instrument:
    ticker: str
    working_schedule: WorkingSchedule
    currency_code: str
    short_name: str
    expected_share: float


def collect_instruments(client: T212ApiClient, pie: Pie) -> List[Instrument]:
    exchange_info = client.get_exchange_info()
    working_schedules = {}
    for ex in exchange_info.values():
        for ws in ex.working_schedules:
            working_schedules[ws.id] = ws

    detailed_instruments = []

    instrument_info = client.get_instrument_info()
    for inst in pie.instruments:
        inst_info = instrument_info[inst.ticker]
        detailed_instruments.append(Instrument(
            ticker=inst_info.ticker,
            working_schedule=working_schedules[inst_info.working_schedule_id],
            currency_code=inst_info.currency_code,
            short_name=inst_info.short_name,
            expected_share=inst.expected_share,
        ))

    return detailed_instruments


def schedule_orders(pie_instruments: List[Instrument], weekly_amount: float, period: datetime.timedelta) -> List[ScheduledOrder]:
    order_since = now()
    order_until = order_since + datetime.timedelta(days=7)

    order_times = []
    cur_time = order_since + period
    while cur_time <= order_until:
        order_times.append(cur_time)
        cur_time += period
    order_times = [t + datetime.timedelta(seconds=(period.total_seconds() / 6) * random.random()) for t in order_times]

    if not order_times:
        raise ValueError('empty order times, adjust period')

    res = []

    for inst in pie_instruments:
        events = inst.working_schedule.time_events
        event_idx = 0

        inst_order_times = []
        for order_time in order_times:
            while event_idx + 1 < len(events) and events[event_idx + 1].date < order_time:
                event_idx += 1
            assert events[event_idx].date < order_time, 'exchange schedule does not cover all orders'
            if events[event_idx].type is not EventType.OPEN:
                continue
            inst_order_times.append(order_time)

        if not inst_order_times:
            raise ValueError(f'couldn\'t prepare order schedule for {inst.short_name}')

        total_amount = weekly_amount * inst.expected_share
        amount_per_order = total_amount / len(inst_order_times)

        res.extend([ScheduledOrder(
            ticker=inst.ticker,
            currency=inst.currency_code,
            amount=round(amount_per_order, 2),
            execute_at=t,
        ) for t in inst_order_times])

    return sorted(res, key=lambda x: (x.execute_at, x.ticker))


def validate_orders(pie_instruments: List[Instrument]) -> bool:
    pie_instruments = {inst.ticker: inst for inst in pie_instruments}
    scheduled_orders = db.scheduled_orders()
    for o in scheduled_orders:
        events = pie_instruments[o.ticker].working_schedule.time_events
        for event, next_event in zip(events, events[1:]):
            if next_event.date < o.execute_at:
                continue
            if event.type is not EventType.OPEN:
                return False
            break
    return True
