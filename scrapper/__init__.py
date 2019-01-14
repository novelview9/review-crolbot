import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
import requests
import json
import asyncio
import itertools
import pandas as pd
from urllib.parse import urlsplit, parse_qs


def smart_store(url, sheet_id, gc):
    store_name = url.split('/')[3]
    store_item_id = url.split('/')[5].split('?')[0].split('#')[0]
    print('get smart_store')
    res = requests.get(f"https://m.smartstore.naver.com/{store_name}/ajax/products/{store_item_id}/purchasereviews/general.json?page.page=ppend_row1&page.size=100000")
    print('finish get smart_store')
    data = json.loads(res.content)['htReturnValue']['content']

    res = requests.get(f"https://m.smartstore.naver.com/{store_name}/ajax/products/{store_item_id}/purchasereviews/premium.json?page.page=ppend_row1&page.size=100000")
    data2 = json.loads(res.content)['htReturnValue']['content']
    df = pd.DataFrame(data + data2).applymap(str).to_csv()
    gc.import_csv(sheet_id, df.encode(encoding='UTF-8'))

def naver_shopping(url, sheet_id, gc):
    def response_to_bs4(response):
        return BeautifulSoup(json.loads(response.content)['htReturnValue']['contents'][0],"html.parser")

    def get_index(contents):
        try:
            start, end = (int(index) for index in contents.select('div')[-1].text.split('다음')[0].strip().split('/'))
        except Exception:
            return 0, 0

        return start, end

    def elemnt_to_dict(comment):
        try:
            date, user = (element.text for element in comment.select('.info_etc span'))
        except Exception:
            date, user = ('', '')
        point = comment.select_one('.num').text
        title = comment.select_one('.info_txt').text
        contents = comment.select_one('.info_txt').text
        images = [image_element.attrs['data-original'].split('?')[0] for image_element in comment.select('img')]
        return dict(date=date, user=user, point=point, title=title, contents=contents, images=images)

    def get_urls(item_id):
        urls = []
        for review_type in ('photo', 'text'):
            response = requests.get(f"https://msearch.shopping.naver.com/detail/review_list.nhn?nvMid={item_id}&section=review&page=1&reviewType={review_type}")
            bs_object = response_to_bs4(response)
            start, end = get_index(bs_object)
            for i in range(start, end+1):
                urls.append(f"https://msearch.shopping.naver.com/detail/review_list.nhn?nvMid={item_id}&section=review&page={i+1}&reviewType={review_type}")
        return urls

    def async_request(index, url):
        result = response_to_bs4(requests.get(url)).select('.list_type_review li._review_list')
        return result

    async def async_get_comment(urls):
        print(len(urls))
        futures = [loop.run_in_executor(None, async_request, index, url) for index, url in enumerate(urls)]
        return await asyncio.gather(*futures)

    params = parse_qs(urlsplit(url).query)
    item_id = params.get('nv_mid')[0]
    urls = get_urls(item_id)
    loop = asyncio.new_event_loop()
    print('start async shopping')
    results = loop.run_until_complete(async_get_comment(urls))
    print('end async shopping')
    comments = []
    for result in results:
        for comment in result:
            comments.append(elemnt_to_dict(comment))

    df = pd.DataFrame(comments).applymap(str).to_csv()
    gc.import_csv(sheet_id, df.encode(encoding='UTF-8'))
