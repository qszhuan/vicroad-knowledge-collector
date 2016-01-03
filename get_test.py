import pickle
import requests
from bs4 import BeautifulSoup
from os import path

question_set = set()
final_list = []

pickle_dict = {'question_set': set(), 'question_list': []}
if path.exists('./question.pickle'):
    with open('./question.pickle', 'rb') as pfile:
        try:
            pickle_dict = pickle.load(pfile)
            question_set = pickle_dict['question_set']
            final_list = pickle_dict['question_list']
            print('loaded', len(question_set), 'questions..')
        except Exception as e:
            print(e)
            pass


def get_questions():
    question_url = 'https://www.vicroads.vic.gov.au/licences/your-ls/get-your-ls/lpt/lptoffline'
    response = requests.get(question_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    questions = soup.find_all("div", {"class": "lpt-area"})[1:]
    ref = soup.find("ul", {'class': 'lpt-printsummary'})
    ref_number = ref.li.contents[1]

    for each in questions:
        answer_img = each.find('div', {'class': 'answer-image'})
        if answer_img.img:
            answer_img.img['src'] = 'https://www.vicroads.vic.gov.au' + answer_img.img['src']

    return ref_number, questions


def get_answer_rows(reference_number):
    answer_url = 'https://www.vicroads.vic.gov.au/licences/your-ls/get-your-ls/lpt/lptoffline/lptcorrectionsheet?testref=' + reference_number
    ref_response = requests.get(answer_url)
    ref_soup = BeautifulSoup(ref_response.content, 'html.parser')
    answers_tbody = ref_soup.find('table', {'class': 'lpt-answersheet'}).tbody
    rows = answers_tbody.findChildren('tr')
    return rows


def write_html(question_answer_list):
    style = """<style>
.hidden-answer:hover{color:red;font-weight:bold;}
.hidden-answer{color:white;display:block;border: 1px solid black;}
</style>"""
    doc_list = ['<html>', style, "<strong>", str(len(question_set)), "</strong>", '</html>']
    doc_list[-1:-1] = [str(each) for each in question_answer_list]

    output = BeautifulSoup(''.join(doc_list), "html.parser")

    with open('b.html', 'w') as f:
        f.write(output.prettify())


def extract_distinct_questions(questions, answer_rows):
    qa_list = []
    for index, question in enumerate(questions):
        question_key = question.text.split('.', maxsplit=1)[1]
        if question_key not in question_set:
            question_set.add(question_key)
            qa_list.append(str(question))
            qa_list.append("{}{}{}".format('<div class="hidden-answer">', answer_rows[index].find('td').text, '</div>'))

    return qa_list


def extract_iterate(loop=10):
    for i in range(loop):
        ref_number, questions = get_questions()
        answer_rows = get_answer_rows(ref_number)
        distinct_questions = extract_distinct_questions(questions, answer_rows)
        print('round(', i, ')', int(len(distinct_questions) / 2), 'questions added.')
        final_list.extend(distinct_questions)

        if distinct_questions:
            print('and saved to disk.')
            with open('./question.pickle', 'wb') as pfile:
                pickle.dump(
                        {
                            'question_set': question_set,
                            'question_list': final_list
                        },
                        pfile)
            print('saved.')

    write_html(final_list)

extract_iterate(100)
