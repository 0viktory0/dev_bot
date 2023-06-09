import logging
import os
import time

from dotenv import load_dotenv
import requests
from telegram import Bot


logger = logging.getLogger()


def get_review(dvmn_token, tg_bot_token, tg_chat_id):
    timestamp = time.time()
    api_url = 'https://dvmn.org/api/long_polling/'
    while True:
        try:
            response = requests.get(
                api_url,
                headers={'Authorization': f'Token {dvmn_token}'},
                params={'timestamp': timestamp},
                timeout=60
            )
            response.raise_for_status()
            reviews = response.json()

            status = reviews.get('status')
            if status == 'found':
                timestamp = reviews['last_attempt_timestamp']
                result = reviews.get('new_attempts')[0]

                title = result['lesson_title']
                url = result['lesson_url']
                if result['is_negative']:
                    result = (
                        'К сожалению, в работе нашлись ошибки.'
                    )
                else:
                    result = (
                        'Преподавателю все понравилось, можно приступать к следующему уроку!'
                    )

                message = 'У Вас проверили работу' \
                          '[{}]({}) \n {}'.format(title, url, result)
                bot = Bot(token=tg_bot_token)

                bot.send_message(
                    chat_id=tg_chat_id,
                    text=message,
                    parse_mode='markdown')
                logging.info('Бот отправил сообщение!')

            elif status == 'timeout':
                timestamp = reviews['timestamp_to_request']

        except requests.exceptions.HTTPError:
            logging.error('Ошибка при выполнении HTTP-запроса')
        except requests.exceptions.ConnectionError:
            logging.error('Ошибка подключения')
            time.sleep(30)
            continue
        except requests.exceptions.ReadTimeout:
            pass


class LogsHandler(logging.Handler):

    def __init__(self, tg_log_bot_token, tg_chat_id):
        super().__init__()
        self.chat_id = tg_chat_id
        self.bot = Bot(tg_log_bot_token)

    def emit(self, record):
        log_entry = self.format(record)
        tg_bot = self.bot
        tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


if __name__ == '__main__':
    load_dotenv()
    dvmn_token = os.environ['DVMN_TOKEN']
    tg_bot_token = os.environ['TG_BOT_TOKEN']
    tg_chat_id = os.environ['TG_CHAT_ID']
    tg_log_bot_token = os.environ['TG_LOG_BOT_TOKEN']


    logger.setLevel(logging.INFO)
    logger.addHandler(LogsHandler(tg_log_bot_token, tg_chat_id))
    logging.info('Бот стартовал!')

    get_review(dvmn_token, tg_bot_token, tg_chat_id)
