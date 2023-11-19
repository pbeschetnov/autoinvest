import telebot
from telebot.formatting import hbold
from telebot.types import Message

import db
from config import *
from utils import *

__all__ = [
    'bot',
    'send_message',
]


class IsAdminFilter(telebot.custom_filters.SimpleCustomFilter):
    key = 'is_admin'

    @staticmethod
    def check(message: Message, **kwargs):
        return message.from_user.id == TELEGRAM_USER


bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode='HTML')
bot.add_custom_filter(IsAdminFilter())


def send_message(text: str):
    if not db.can_send_message(text):
        return
    bot.send_message(TELEGRAM_USER, text)
    db.record_message(text)


@bot.message_handler(is_admin=True, commands=['start'])
def start(message: Message):
    bot.send_message(message.from_user.id, f'Howdy! Let\'s autoinvest!')
    return status(message)


@bot.message_handler(is_admin=True, commands=['status'])
def status(message: Message):
    enabled = db.enabled()
    s = hbold('enabled' if db.enabled() else 'disabled')
    text = f'AutoInvest is {s}.'
    if enabled and (t := db.next_order_scheduled_for()):
        text += f' Next order is scheduled for {t.astimezone(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")}.'
    bot.send_message(message.from_user.id, text)


@bot.message_handler(is_admin=True, commands=['enable'])
def enable(message: Message):
    db.enable()
    return status(message)


@bot.message_handler(is_admin=True, commands=['disable'])
def disable(message: Message):
    db.disable()
    return status(message)


def main():
    setup_logging(filename='telegram.log')
    bot.infinity_polling()


if __name__ == '__main__':
    main()
