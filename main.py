import collections
import logging
import time
import traceback

from telebot.formatting import hpre

import db
from api_client import T212ApiClient
from config import *
from equity_client import *
from scheduler import *
from telegram import send_message
from utils import *


def run(equity: EquityClient, api_client: T212ApiClient):
    # Checking if current state has changed.
    pie = api_client.find_pie(AUTOINVEST_PIE)
    if not pie:
        logging.warning('"%s" pie is not found', AUTOINVEST_PIE)
        return
    pie_composition = sorted([(inst.ticker, inst.expected_share) for inst in pie.instruments])
    if (state := build_state(pie_composition)) != db.state():
        logging.info('state has changed, updating')
        db.update_state(state)

    # Validate scheduled order in case market open times have changed.
    db.drop_expired_scheduled_orders()
    pie_instruments = collect_instruments(api_client, pie)
    if not validate_orders(pie_instruments):
        logging.info('some orders scheduled when market is closed, invalidating')
        db.drop_scheduled_orders()

    # Scheduling new orders.
    if not db.scheduled_order_count():
        logging.info('scheduling new orders')
        scheduled_orders = schedule_orders(pie_instruments, WEEKLY_AMOUNT, INVESTMENT_PERIOD)
        db.put_scheduled_orders(*scheduled_orders)

    # Executing orders.
    pending_orders = None
    for o in db.scheduled_orders_to_execute():
        def postpone():
            with db.connection() as conn, conn.transaction():
                db.add_leftovers(o.ticker, o.amount, conn=conn)
                db.delete_scheduled_order(o, conn=conn)

        amount = round(o.amount + db.leftovers(o.ticker), 2)
        logging.info('executing order for %s: %s %s', o.ticker, amount, MASTER_CURRENCY)

        if pending_orders is None:
            pending_orders = collections.defaultdict(list)
            for po in equity.pending_orders():
                pending_orders[po.ticker].append(po)
        if o.ticker in pending_orders:
            logging.error('%s still has some pending orders: %s', o.ticker, pending_orders[o.ticker])
            send_message(f'{o.ticker} still has some pending orders created at ' +
                         hpre(', '.join(po.created_at.astimezone(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S') for po in pending_orders[o.ticker])))
            postpone()
            continue

        executed, saved = False, False
        try:
            order = equity.execute_order(o.ticker, o.currency, amount)
            executed = True

            with db.connection() as conn, conn.transaction():
                db.put_orders(order, conn=conn)
                db.delete_scheduled_order(o, conn=conn)
                db.drop_leftovers(o.ticker, conn=conn)
            saved = True
            logging.info('executed using %s %s', order.amount, order.currency)
        except SmolOrderException:
            logging.info('order amount is too small, postponing')
            postpone()
        except InsufficientFundsException:
            logging.info('account balance is insufficient, skipping order')
            send_message('Account balance is insufficient to execute new orders.')
            db.delete_scheduled_order(o)
        finally:
            if executed and not saved:
                logging.error('failed to save executed %s order, disabling autoinvest to avoid uncontrolled spendings', o.ticker)
                send_message(f'Failed to save executed {o.ticker} order, disabling autoinvest to avoid uncontrolled spendings.')
                db.disable()


def main():
    setup_logging(filename='main.log')

    logging.info('initializing clients')
    equity = EquityClient()
    api_client = T212ApiClient()

    logging.info('running main loop')
    while True:
        if db.enabled():
            try:
                run(equity, api_client)
            except CookiesExpiredException:
                logging.info('cookies has expired, restarting')
                return
            except Exception:
                logging.error('unexpected error running main loop: %s', traceback.format_exc())
                send_message(f'Unexpected error running main loop:\n{hpre(traceback.format_exc())}')
                raise
        else:
            db.drop_scheduled_orders()

        time.sleep(60)


if __name__ == '__main__':
    main()
