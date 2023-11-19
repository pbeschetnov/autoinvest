import json
import logging
import shutil
import time
from typing import Optional, List, Any

import requests
from pytrading212 import Equity, EquityOrder
from pytrading212 import OrderType
from pytrading212 import constants
from selenium import webdriver
from selenium.common import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_not_exception_type

from config import *
from models import orders
from utils import *

__all__ = [
    'SmolOrderException',
    'CookiesExpiredException',
    'InsufficientFundsException',
    'EquityClient',
]


class SmolOrderException(Exception):
    pass


class CookiesExpiredException(Exception):
    pass


class InsufficientFundsException(Exception):
    pass


class EquityPatched(Equity):
    USER_AGENT = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/116.0.0.0 Safari/537.36')
    T212_COOKIES_FILENAME = '.secrets/t212_cookies'
    USER_DATA_DIR = '.secrets/browser_data'

    @retry(reraise=True, stop=stop_after_attempt(3), wait=wait_exponential(max=15))
    def __init__(self):
        self.session = f'TRADING212_SESSION_{MODE.name}'
        self.base_url = f'https://{MODE.name.lower()}.trading212.com'

        # Checking if current cookies are still working.
        self._load_cookies()
        if self._cookies_valid():
            logging.info('using cached T212 cookies')
            return

        self.driver = self._build_driver()
        try:
            # Checking if still logged in.
            self._refresh_cookies()
            if self._cookies_valid():
                logging.info('still logged in, using refreshed T212 cookies')
                self._dump_cookies()
                return

            logging.info('acquiring new T212 cookies')
            self._login()
            self._dump_cookies()
        finally:
            self.driver.quit()
            pass

    @retry(reraise=True, stop=stop_after_attempt(15), wait=wait_exponential(max=15))
    def switch_to(self, trading: constants.Trading):
        super().switch_to(trading)

    def _build_driver(self) -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--start-maximized')
        options.add_argument('--window-size=1280,783')
        options.add_argument('--enable-file-cookies')
        options.add_argument(f'--user-data-dir={self.USER_DATA_DIR}')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-internal-flash')
        options.add_argument('--disable-plugins-discovery')
        options.add_argument('--proxy-server="direct://"')
        options.add_argument('--proxy-bypass-list=*')
        options.add_argument('--no-sandbox')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--blink-settings=imagesEnabled=false')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument(f'user-agent={self.USER_AGENT}')
        try:
            return webdriver.Chrome(options=options)
        except WebDriverException:
            try:
                shutil.rmtree(self.USER_DATA_DIR)
            except FileNotFoundError:
                pass
            raise

    def _refresh_cookies(self):
        self.driver.get(self.base_url)
        # Waiting either for account menu if logged in or "Open Account" button if not.
        self._wait_trading_page_load('.account-menu-info', '[qa-data-button="header-open-account-btn"]')
        try:
            self.driver.find_element(By.CLASS_NAME, 'account-menu-info')
        except NoSuchElementException:
            return
        self.switch_to(constants.Trading.EQUITY)
        self._extract_cookies()

    def _login(self):
        self.driver.get(constants.URL_LOGIN)

        # Click Accept all cookies if it appears.
        try:
            self.driver.find_element(By.CLASS_NAME, constants.CLASS_COOKIES_NOTICE_BUTTON).click()
        except NoSuchElementException:
            pass  # ignore

        # Authenticate
        WebDriverWait(self.driver, 5).until(expected_conditions.visibility_of_element_located((By.NAME, 'email')))
        self.driver.find_element(By.NAME, 'email').send_keys(EMAIL)
        self.driver.find_element(By.NAME, 'password').send_keys(PASSWORD)

        # Click login button
        self.driver.find_element(By.CLASS_NAME, constants.CLASS_LOGIN_BUTTON).click()

        # Wait until the site is fully loaded, 120 seconds is a lot, but the site sometimes is very slow
        self._wait_trading_page_load('.account-menu-info')

        # Redirect to correct mode, DEMO or LIVE
        if MODE.name not in self.driver.current_url:
            self.driver.get(self.base_url)
            self._wait_trading_page_load('.account-menu-info')

        # Switch to right trading session: CFD or EQUITY
        self.switch_to(constants.Trading.EQUITY)
        self._extract_cookies()

    def _extract_cookies(self):
        if (cookies := self.driver.get_cookies()) is not None:
            for cookie in cookies:
                if self.session in cookie['name']:
                    self.cookie = f'{self.session}={cookie["value"]};'
                    break
        else:
            raise Exception('unable to get cookies, aborting.')
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': self.driver.execute_script('return navigator.userAgent;'),
            'Cookie': self.cookie,
        }

    def _dump_cookies(self):
        with open(self.T212_COOKIES_FILENAME, 'w') as f:
            json.dump(self.headers, f)

    def _load_cookies(self):
        try:
            with open(self.T212_COOKIES_FILENAME, 'r') as f:
                self.headers = json.load(f)
        except Exception:
            pass

    def _cookies_valid(self) -> bool:
        try:
            r = self.get_funds()
        except Exception:
            return False
        if r.get('code'):
            return False
        return True

    def _wait_trading_page_load(self, *selectors: str):
        WebDriverWait(self.driver, 120). \
            until(expected_conditions.visibility_of_element_located(
            (By.CSS_SELECTOR, ','.join(selectors))))
        time.sleep(5)


class EquityClient:
    def __init__(self):
        self._equity = EquityPatched()
        self._session = requests.session()
        self._session.headers.update(self._equity.headers)

    def convert(self, currency_from: str, currency_to: str, amount: float) -> float:
        if currency_from == currency_to:
            return amount
        r = self._api_call(
            'POST', '/rest/trading/v1/fx-rates/conversion',
            json={
                'fromCurrency': currency_from,
                'toCurrency': currency_to,
                'amount': amount,
            },
        )
        return r['value']

    def pending_orders(self) -> List[orders.Order]:
        r = self._api_call('POST', '/rest/trading/v1/accounts/summary', json=[])
        return [orders.Order.from_dict(o) for o in r.get('valueOrders', {}).get('items', [])]

    def execute_order(self, ticker: str, currency: str, amount: float) -> Optional[orders.Order]:
        order = EquityOrder(
            instrument_code=ticker,
            order_type=OrderType.MARKET,
            value=0,
        )

        currencies = (currency,) + CURRENCY_PRIORITY
        for currency in currencies:
            order.currency = currency
            order.value = round(self.convert(MASTER_CURRENCY, currency, amount), 2)

            r = self._equity.execute_order(order)
            if r.get('code'):
                if r['code'] == 'BusinessException' and r.get('context', {}).get('type') in ['AccountWalletNotFound', 'InsufficientFreeForStocksBuyValue']:
                    logging.info('insufficient funds of %s when buying %s', currency, ticker)
                    continue
                if r['code'] == 'BusinessException' and r.get('context', {}).get('type') == 'MinValueExceeded':
                    raise SmolOrderException(r.get('message'))
                if r['code'] == 'AuthenticationFailed':
                    raise CookiesExpiredException()
                raise RuntimeError(f'unknown error while executing order: {r}')

            return orders.Order(
                ticker=ticker,
                amount=order.value,
                currency=currency,
                created_at=now(),
            )

        raise InsufficientFundsException()

    @retry(reraise=True, retry=retry_if_not_exception_type(CookiesExpiredException), stop=stop_after_attempt(5), wait=wait_exponential(max=30))
    def _api_call(self, method: str, path: str, **kwargs) -> Any:
        r = self._session.request(method, f'{self._equity.base_url}{path}', **kwargs)
        if r.status_code == 401:
            raise CookiesExpiredException()
        r.raise_for_status()
        data = r.json()
        if data.get('code'):
            raise ValueError(data)
        return data
