from flask import Flask, json, request, Response
import time
from threading import Thread
from sheet import get_sheet
from scrapper import smart_store, naver_shopping
from multiprocessing import Process
import pydash
import requests
from sheet import gc
from zappa.async import task
from flask import jsonify


app = Flask(__name__)
slack_token = ''

def response_slack(text, attachments=[]):
    requests.post(
        '',
        json=dict(text=text, attachments=attachments)
    )

@task
def run_scrapper(url, username):
    sheet, sheet_link = get_sheet()
    sheet_id = sheet.id
    response_slack(f'{sheet_link} 해당 엑셀 시트로 요청하신 데이터가 업로드 됩니다.(완료 시 알람)')
    if 'smartstore' in url:
        smart_store(url, sheet_id, gc)
    elif 'shopping.naver' in url:
        naver_shopping(url, sheet_id, gc)

    response_slack(f'업데이트 완료 <@{username}>')


@app.route('/',  methods = ['POST'])
def message(*args, **kwargs):
    url = pydash.get(request, 'form.text')
    username = pydash.get(request, 'form.user_name')
    if not any(word in url for word in ('smartstore', 'shopping.naver.com')):
        return jsonify({
            'text': '잘못된 주소 유형입니다. (now support smartstore.naver.com, shopping.naver.com)'
        })

    run_scrapper(url, username)
    return jsonify({
        "text": f'{url} 주소에 대한 요청을 확인했습니다.',
    })


if __name__ == '__main__':
    app.run()
