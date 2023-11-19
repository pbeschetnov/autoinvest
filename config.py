import datetime

from dateutil.tz import gettz
from pytrading212.constants import Mode

__all__ = [
    'MODE',
    'EMAIL',
    'PASSWORD',
    'T212_TOKEN',
    'PG_PASSWORD',
    'TELEGRAM_USER',
    'TELEGRAM_TOKEN',
    'AUTOINVEST_PIE',
    'MASTER_CURRENCY',
    'CURRENCY_PRIORITY',
    'WEEKLY_AMOUNT',
    'INVESTMENT_PERIOD',
    'TIMEZONE',
    'MAX_MESSAGES_PER_HOUR',
]

MODE = Mode.LIVE
if MODE is Mode.LIVE:
    T212_TOKEN = open('.secrets/t212_live_token', 'r').read().strip()
else:
    T212_TOKEN = open('.secrets/t212_demo_token', 'r').read().strip()

EMAIL = open('.secrets/t212_email', 'r').read().strip()
PASSWORD = open('.secrets/t212_password', 'r').read().strip()
PG_PASSWORD = open('.secrets/pg_password', 'r').read().strip()
TELEGRAM_USER = int(open('.secrets/telegram_user', 'r').read().strip())
TELEGRAM_TOKEN = open('.secrets/telegram_token', 'r').read().strip()

AUTOINVEST_PIE = 'autoinvest'
MASTER_CURRENCY = 'EUR'
CURRENCY_PRIORITY = ('EUR', 'USD')
WEEKLY_AMOUNT = 1250  # in master currency
INVESTMENT_PERIOD = datetime.timedelta(hours=1)

TIMEZONE = gettz('Europe/Amsterdam')
MAX_MESSAGES_PER_HOUR = 5
