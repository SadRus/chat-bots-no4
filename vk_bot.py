import os
import random
import re

import redis
import vk_api as vk

from dotenv import load_dotenv
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from quiz import create_quiz


def create_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.PRIMARY)
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
    right_answer = questions[cache.get(user_id)]
    vk_api.messages.send(
        user_id=user_id,
        random_id=get_random_id(),
        message=f'{question} \n {right_answer}',
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

    cache = redis.Redis(
        host='localhost',
        port=6379,
        decode_responses=True,
    )

    vk_group_token = os.getenv('VK_GROUP_TOKEN')
    vk_session = vk.VkApi(token=vk_group_token)
    vk_api = vk_session.get_api()
    questions = create_quiz()

    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == 'Новый вопрос':
                handle_new_question_request(event, vk_api, cache, questions)
                continue
            if event.text == 'Сдаться':
                surrender(event, vk_api, cache, questions)
                continue
            if event.text == 'Мой счет':
                pass
            handle_solution_attempt(event, vk_api, cache, questions)


if __name__ == '__main__':
    main()
