import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import HTTPException

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

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
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    logging.debug('Начинаем отправку сообщения')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение успешно отправлено')
    except telegram.error.TelegramError as error:
        logging.error(f'Ошибка отправки сообщения: {error}')


def get_api_answer(timestamp):
    """Запрос к API сервиса Практикум.Домашка."""
    logging.debug('Начали запрос к API')
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp})
        if response.status_code != HTTPStatus.OK:
            raise HTTPException(
                f'Запрос к API выдает код {response.status_code}')
        return response.json()
    except requests.RequestException as error:
        logging.error(f'Ошибка запроса к API: {error}')


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Ответ не в виде словаря')
    if 'homeworks' not in response:
        raise KeyError('Отсутствует ключ "homeworks"')
    if 'current_date' not in response:
        raise KeyError('Отсутствует ключ "current_date"')
    homework = response['homeworks']
    if not isinstance(homework, list):
        raise TypeError('Данные не в виде списка')
    return homework


def parse_status(homework):
    """Проверка статуса."""
    status = homework.get('status')
    if 'homework_name' not in homework:
        raise KeyError('Отсутствует название работы')
    if 'status' not in homework:
        raise KeyError('Отсутствует статус работы')
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Неожиданный статус работы {status}')
    homework_name = homework.get('homework_name')
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутствует обязательная переменная окружения')
        sys.exit('Отсутствуют переменные окружения, остановка бота')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_message = ''
    while True:
        try:
            response = get_api_answer(timestamp - 3000000)
            homework = check_response(response)
            if homework[0]:
                message = parse_status(homework[0])
                if message != last_message:
                    send_message(bot, message)
                    last_message = message
            else:
                logging.debug('Домашние работы отсутствуют')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.exception(message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
