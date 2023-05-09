import logging
import os
import random
import re
import redis
import telegram

from dotenv import load_dotenv
from functools import partial
from telegram.ext import (
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

from create_argparser import create_parser
from tg_handlers import TelegramLogsHandler
from quiz import create_quiz


logger = logging.getLogger('tg_bot_no4_logger')


def start(update, context):
    start_keyboard = [
        ['Новый вопрос', 'Сдаться'],
        ['Мой счет'],
    ]
    reply_markup = telegram.ReplyKeyboardMarkup(start_keyboard)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Hello, squizers!\nНажмите "Новый вопрос" для начала викторины.',
        reply_markup=reply_markup,
    )


def handle_new_question_request(update, context, cache, questions):
    user_id = update.effective_chat.id
    question = random.choice(list(questions))
    cache.set(user_id, question)

    pattern = '\\.|\\('
    right_answer = re.split(pattern, questions[cache.get(user_id)])[0]
    context.user_data['right_answer'] = right_answer
    context.user_data['questions'] = questions

    update.message.reply_text(
        f'{question}'
    )


def handle_solution_attempt(update, context):
    user_input = update.message.text
    right_answer = context.user_data['right_answer']

    if user_input.lower() == right_answer.lower():
        update.message.reply_text(
            'Правильно! Поздравляю!'
            'Для следующего вопроса нажми «Новый вопрос»'
        )
    else:
        update.message.reply_text(
            'Неправильно… Попробуешь ещё раз?'
        )


def surrender(update, context, cache):
    right_answer = context.user_data['right_answer']
    questions = context.user_data['questions']
    update.message.reply_text(f'Правильный ответ: {right_answer}')
    return handle_new_question_request(update, context, cache, questions)


def main():
    load_dotenv()
    parser = create_parser()
    args = parser.parse_args()

    tg_bot_token = os.getenv('TG_BOT_TOKEN')
    tg_bot_logger_token = os.getenv('TG_BOT_LOGGER_TOKEN')
    tg_chat_id = os.getenv('TG_CHAT_ID')

    cache = redis.Redis(
        host='localhost',
        port=6379,
        decode_responses=True,
        db=0,
    )

    tg_bot_logger = telegram.Bot(token=tg_bot_logger_token)
    logs_full_path = os.path.join(args.dest_folder, 'tg_bot_no4.log')
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

    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher

    questions = create_quiz()

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(
        MessageHandler(Filters.regex('^Новый вопрос$'),
                       partial(handle_new_question_request, cache=cache,
                               questions=questions))
    )
    dispatcher.add_handler(
        MessageHandler(Filters.regex('^Сдаться$'),
                       partial(surrender, cache=cache))
    )
    dispatcher.add_handler(
        MessageHandler(Filters.text & ~Filters.command,
                       handle_solution_attempt)
    )

    try:
        updater.start_polling()
        logger.info('Telegram chat-bot #4 @dvmnQuizbotbot started')
    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    main()
