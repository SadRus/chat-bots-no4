import logging
import os
import random
import re

import redis
import telegram
import vk_api as vk

from dotenv import load_dotenv
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from create_argparser import create_parser
from tg_handlers import TelegramLogsHandler
from quiz import create_quiz


logger = logging.getLogger('vk_bot_no4_logger')


def create_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет')
    return keyboard


def echo(event, vk_api):
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        message=event.text,
        keyboard=create_keyboard().get_keyboard(),
    )


def handle_new_question_request(event, vk_api, cache, questions):
    user_id = event.user_id
    question = random.choice(list(questions))
    cache.set(user_id, question)
    vk_api.messages.send(
        user_id=user_id,
        random_id=get_random_id(),
        message=f'{question}',
        keyboard=create_keyboard().get_keyboard(),
    )


def handle_solution_attempt(event, vk_api, cache, questions):
    user_id = event.user_id
    pattern = '\\.|\\('
    right_answer = re.split(pattern, questions[cache.get(user_id)])[0]
    if event.text.lower() == right_answer.lower():
        vk_api.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            message='Правильно! Поздравляю!'
                    'Для следующего вопроса нажми «Новый вопрос»',
            keyboard=create_keyboard().get_keyboard(),
        )
    else:
        vk_api.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            message='Неправильно… Попробуешь ещё раз?',
            keyboard=create_keyboard().get_keyboard(),
        )


def surrender(event, vk_api, cache, questions):
    user_id = event.user_id
    right_answer = questions[cache.get(user_id)]

    vk_api.messages.send(
        user_id=user_id,
        random_id=get_random_id(),
        message=f'Правильный ответ: {right_answer}',
        keyboard=create_keyboard().get_keyboard(),
    )
    return handle_new_question_request(event, vk_api, cache, questions)


def main():
    load_dotenv()
    parser = create_parser()
    args = parser.parse_args()

    tg_bot_logger_token = os.getenv('TG_BOT_LOGGER_TOKEN')
    tg_chat_id = os.getenv('TG_CHAT_ID')
    vk_group_token = os.getenv('VK_GROUP_TOKEN')

    tg_bot_logger = telegram.Bot(token=tg_bot_logger_token)

    logs_full_path = os.path.join(args.dest_folder, 'vk_bot_no4.log')
    os.makedirs(args.dest_folder, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        filename=logs_full_path,
        filemode='w',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    logger.setLevel(logging.INFO)
    handler = TelegramLogsHandler(
        logs_full_path,
        tg_bot=tg_bot_logger,
        chat_id=tg_chat_id,
        maxBytes=args.max_bytes,
        backupCount=args.backup_count,
    )
    logger.addHandler(handler)
    cache = redis.Redis(
        host='localhost',
        port=6379,
        decode_responses=True,
        db=1,
    )

    vk_group_token = os.getenv('VK_GROUP_TOKEN')
    vk_session = vk.VkApi(token=vk_group_token)
    vk_api = vk_session.get_api()
    questions = create_quiz()

    longpoll = VkLongPoll(vk_session)
    logger.info('Vk group chat-bot #4 started')
    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text == 'Новый вопрос':
                    handle_new_question_request(
                        event, vk_api, cache, questions
                    )
                    continue
                if event.text == 'Сдаться':
                    surrender(event, vk_api, cache, questions)
                    continue
                if event.text == 'Мой счет':
                    pass
                handle_solution_attempt(event, vk_api, cache, questions)
    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    main()
