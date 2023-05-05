import os
import random
import re
import redis
import telegram

from dotenv import load_dotenv
from functools import partial
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    Updater,
)
from states import State
from quiz import create_quiz


quiz_questions = create_quiz()

start_keyboard = [
    ['Новый вопрос', 'Сдаться'],
    ['Мой счет'],
]
reply_markup = telegram.ReplyKeyboardMarkup(start_keyboard)


def start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Hello, squizers!',
        reply_markup=reply_markup,
    )
    return State.MAIN_MENU


def handle_new_question_request(update, context, db):
    user_id = update.effective_chat.id
    question = random.choice(list(quiz_questions))
    db.set(user_id, question)

    pattern = '\\.|\\('
    right_answer = re.split(pattern, quiz_questions[db.get(user_id)])[0]
    context.user_data['right_answer'] = right_answer

    update.message.reply_text(
        f'{question}'
    )
    return State.ANSWER


def handle_solution_attempt(update, context, db):
    user_input = update.message.text
    right_answer = context.user_data['right_answer']

    if user_input.lower() == right_answer.lower():
        update.message.reply_text(
            'Правильно! Поздравляю!'
            'Для следующего вопроса нажми «Новый вопрос»'
        )
        return State.MAIN_MENU
    else:
        update.message.reply_text(
            'Неправильно… Попробуешь ещё раз?'
        )


def get_statistic(update, context):
    pass


def surrender(update, context, db):
    right_answer = context.user_data['right_answer']
    update.message.reply_text(
        f'Правильный ответ {right_answer}'
    )
    return handle_new_question_request(update, context, db)


def main():
    load_dotenv()

    quiz_storage = redis.Redis(
        host='localhost',
        port=6379,
        decode_responses=True,
    )
    tg_bot_token = os.getenv('TG_BOT_TOKEN')

    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start)
        ],
        states={
            State.MAIN_MENU: [
                MessageHandler(Filters.regex('^Новый вопрос$'),
                               partial(handle_new_question_request, db=quiz_storage)),
                MessageHandler(Filters.regex('^Мой счет$'), get_statistic)
            ],
            State.ANSWER: [
                MessageHandler(Filters.regex('^Сдаться$'),
                               partial(surrender, db=quiz_storage)),
                MessageHandler(Filters.text & ~Filters.command,
                               partial(handle_solution_attempt, db=quiz_storage)),
            ],
        },
        fallbacks=[CommandHandler('start', start)]
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
