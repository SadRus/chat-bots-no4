from pprint import pprint


with open('./quiz-questions/1vs1201.txt', 'r', encoding='KOI8-R') as file:
    text = file.read()

# for text in text.split('\n\n'):
    # print(text)
    # print()
quiz_content = text.split('\n\n')
#print(text)
quiz = {}

for text in quiz_content:
    if 'вопрос' in text.lower():
        question = text
    if 'ответ' in text.lower():
        answer = text
        quiz[question] = answer

pprint(quiz)
