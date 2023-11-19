import datetime
import functools
from typing import Tuple, List, ParamSpec, TypeVar, Callable, Optional, Any

from psycopg import Connection
from psycopg.rows import class_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from config import *
from models.orders import Order, ScheduledOrder
from utils import *

__all__ = [
    'connection',
    'put_scheduled_orders',
    'drop_scheduled_orders',
    'scheduled_order_count',
    'scheduled_orders_to_execute',
    'next_order_scheduled_for',
    'delete_scheduled_order',
    'leftovers',
    'add_leftovers',
    'drop_leftovers',
    'put_orders',
    'state',
    'update_state',
    'enabled',
    'enable',
    'disable',
]

_settings = {
    'user': 'autoinvest',
    'password': PG_PASSWORD,
    'dbname': 'autoinvest',
    'host': '127.0.0.1',
    'port': '5432',
}
_pool = ConnectionPool(' '.join(f'{k}={v}' for k, v in _settings.items()), min_size=1, max_size=8, max_idle=4)

connection = _pool.connection

P = ParamSpec('P')
R = TypeVar('R')


def with_conn(func: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        conn = kwargs.get('conn')
        if conn:
            return func(*args, **kwargs)
        with connection() as conn, conn.transaction():
            return func(*args, **kwargs, conn=conn)

    return wrapper


@with_conn
def put_scheduled_orders(*orders: ScheduledOrder, conn: Connection = None):
    conn.cursor().executemany(
        '''insert into scheduled_orders (ticker, currency, amount, execute_at)
        values (%s, %s, %s, %s)''',
        [(o.ticker, o.currency, o.amount, o.execute_at) for o in orders],
    )


@with_conn
def drop_scheduled_orders(conn: Connection = None):
    conn.execute('delete from scheduled_orders')


@with_conn
def drop_expired_scheduled_orders(conn: Connection = None):
    conn.execute('delete from scheduled_orders where execute_at < %s', (now() - INVESTMENT_PERIOD,))


@with_conn
def scheduled_order_count(conn: Connection = None) -> int:
    return conn. \
        execute('select count(1) from scheduled_orders'). \
        fetchone()[0]


@with_conn
def scheduled_orders(conn: Connection = None) -> List[ScheduledOrder]:
    return conn. \
        cursor(row_factory=class_row(ScheduledOrder)). \
        execute('select * from scheduled_orders'). \
        fetchall()


@with_conn
def scheduled_orders_to_execute(conn: Connection = None) -> List[ScheduledOrder]:
    return conn. \
        cursor(row_factory=class_row(ScheduledOrder)). \
        execute('select * from scheduled_orders where execute_at <= %s', (now(),)). \
        fetchall()


@with_conn
def next_order_scheduled_for(conn: Connection = None) -> Optional[datetime.datetime]:
    return conn. \
        execute('select min(so.execute_at) from scheduled_orders as so'). \
        fetchone()[0]


@with_conn
def delete_scheduled_order(order: ScheduledOrder, conn: Connection = None):
    conn.execute(
        'delete from scheduled_orders where ticker = %s and execute_at = %s',
        (order.ticker, order.execute_at),
    )


@with_conn
def leftovers(ticker: str, conn: Connection = None) -> float:
    row = conn.execute('select amount from leftovers where ticker = %s', (ticker,)).fetchone()
    return (row or [0.0])[0]


@with_conn
def add_leftovers(ticker: str, leftover_amount: float, conn: Connection = None):
    if not leftover_amount:
        return
    conn.execute(
        '''insert into leftovers as t (ticker, amount) values (%s, %s)
        on conflict (ticker) do update set amount = t.amount + %s''',
        (ticker, leftover_amount, leftover_amount),
    )


@with_conn
def drop_leftovers(ticker: str, conn: Connection = None):
    conn.execute('delete from leftovers where ticker = %s', (ticker,))


@with_conn
def put_orders(*orders: Order, conn: Connection = None):
    conn.cursor().executemany(
        'insert into orders (ticker, amount, currency, created_at) values (%s, %s, %s, %s)',
        [(o.ticker, o.amount, o.currency, o.created_at) for o in orders],
    )


@with_conn
def state(conn: Connection = None) -> List[Tuple[str, str]]:
    return conn.execute('select * from state order by key').fetchall()


@with_conn
def update_state(state: List[Tuple[str, str]], conn: Connection = None):
    conn.execute('delete from state')
    conn.cursor().executemany('insert into state (key, value) values (%s, %s)', state)
    drop_scheduled_orders(conn=conn)


@with_conn
def enabled(conn: Connection = None) -> bool:
    return _metadata_get('enabled', conn) is True


@with_conn
def enable(conn: Connection = None):
    _metadata_set('enabled', True, conn)


@with_conn
def disable(conn: Connection = None):
    _metadata_set('enabled', False, conn)


@with_conn
def can_send_message(text: str, conn: Connection = None) -> bool:
    rows = conn. \
        execute('select text from messages where sent_at > %s', (now() - datetime.timedelta(hours=1),)). \
        fetchall()
    sent_messages = [row[0] for row in rows]
    return len(sent_messages) < MAX_MESSAGES_PER_HOUR and text not in sent_messages


@with_conn
def record_message(text: str, conn: Connection = None):
    conn.execute('insert into messages (text, sent_at) values (%s, %s)', (text, now()))
    conn.execute('delete from messages where sent_at < %s', (now() - datetime.timedelta(hours=1),))


def _metadata_get(key: str, conn: Connection) -> Any:
    row = conn.execute('select value from metadata where key = %s', (key,)).fetchone()
    if row:
        return row[0]


def _metadata_set(key: str, value: Any, conn: Connection):
    conn.execute(
        '''insert into metadata (key, value) values (%s, %s)
        on conflict (key) do update set value = excluded.value''',
        (key, Jsonb(value)),
    )
