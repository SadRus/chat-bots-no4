import glob
import os


def create_quiz():
    quiz_file_paths = glob.glob(
        f'{os.getenv("QUIZ_QUESTIONS_PATH")}*.txt',
    )
    quiz_questions = {}
    for path in quiz_file_paths:
        with open(path, 'r', encoding='KOI8-R') as file:
            quiz_content = file.read()

        quiz_content = quiz_content.split('\n\n')
        for text in quiz_content:
            if text.lower().startswith('вопрос'):
                question = text
            if text.lower().startswith('ответ'):
                answer = text.split('\n')[1]
                quiz_questions[question] = answer
    return quiz_questions
