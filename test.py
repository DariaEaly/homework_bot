import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Updater

from exceptions import NoTokensException

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s',
)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка доступности переменных окружения."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID is not None:
        return True
    else:
        raise NoTokensException('Отсутствуют необходимые переменные окружения')


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(timestamp):
    """Запрос к API сервиса Практикум.Домашка."""
    payload = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=payload).json()
    return response


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    try:
        pass
    except TypeError:
        pass
    homework = response.get('homeworks')
    return homework

def parse_status(homework):
    """Проверка статуса."""
    status = homework[0].get('status')
    homework_name = homework[0].get('homework_name')
    if status in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'

bot = Bot(token=TELEGRAM_TOKEN)
timestamp = 0
check_tokens()
response = get_api_answer(timestamp)
homework = check_response(response)
message = parse_status(homework)
print('!!!')
print(message)
print('!!!')
parse_status(homework)