import datetime
import time
from typing import Dict, Iterable

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config import *
from models import exchanges, pies, instruments
from utils import cached_method

__all__ = [
    'T212ApiClient',
]


class T212ApiClient:
    def __init__(self):
        self._endpoint = f'https://{MODE.name.lower()}.trading212.com'
        self._session = requests.session()
        self._session.headers.update({
            'Authorization': T212_TOKEN,
        })

    def get_pies(self) -> Iterable[pies.Pie]:
        _pies = self._get('/api/v0/equity/pies')
        for pie in _pies:
            time.sleep(5)  # rate limiting
            yield pies.Pie.from_dict(self._get_pie(pie['id']))

    def find_pie(self, name: str) -> pies.Pie:
        for pie in self.get_pies():
            if pie.settings.name == name:
                return pie

    @cached_method(ttl=datetime.timedelta(hours=3))
    def get_exchange_info(self) -> Dict[int, exchanges.Exchange]:
        _exchanges = self._get('/api/v0/equity/metadata/exchanges')
        return {e['id']: exchanges.Exchange.from_dict(e) for e in _exchanges}

    @cached_method(ttl=datetime.timedelta(hours=3))
    def get_instrument_info(self) -> Dict[str, instruments.Instrument]:
        _instruments = self._get('/api/v0/equity/metadata/instruments')
        return {i['ticker']: instruments.Instrument.from_dict(i) for i in _instruments}

    @retry(reraise=True, stop=stop_after_attempt(15), wait=wait_exponential(max=60))
    def _get(self, path):
        r = self._session.get(f'{self._endpoint}{path}')
        r.raise_for_status()
        return r.json()

    def _get_pie(self, pie_id: int):
        return self._get(f'/api/v0/equity/pies/{pie_id}')
