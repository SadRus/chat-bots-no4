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


def start(update, context):
    start_keyboard = [
        ['Новый вопрос', 'Сдаться'],
        ['Мой счет'],
    ]
    reply_markup = telegram.ReplyKeyboardMarkup(start_keyboard)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Hello, squizers!',
        reply_markup=reply_markup,
    )
    return State.MAIN_MENU


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
    return State.ANSWER


def handle_solution_attempt(update, context):
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


def surrender(update, context, cache):
    right_answer = context.user_data['right_answer']
    questions = context.user_data['questions']

    update.message.reply_text(f'Правильный ответ: {right_answer}')
    return handle_new_question_request(update, context, cache, questions)


def main():
    load_dotenv()

    cache = redis.Redis(
        host='localhost',
        port=6379,
        decode_responses=True,
        db=0,
    )
    tg_bot_token = os.getenv('TG_BOT_TOKEN')
    questions = create_quiz()

    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher

    questions_handler = ConversationHandler(
        entry_points=[
            MessageHandler(Filters.regex('^Новый вопрос$'),
                           partial(handle_new_question_request,
                                   cache=cache,
                                   questions=questions)),
        ],
        states={
            State.ANSWER: [
                MessageHandler(Filters.regex('^Сдаться$'),
                               partial(surrender, cache=cache)),
                MessageHandler(Filters.text & ~Filters.command,
                               handle_solution_attempt),
            ],
            State.MAIN_MENU: [
                MessageHandler(Filters.regex('^Мой счет$'), get_statistic)
            ],
        },
        fallbacks=[CommandHandler('start', start)],
        allow_reentry=True,
    )

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(questions_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
