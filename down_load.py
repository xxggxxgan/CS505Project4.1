import os
import re
import sys
import json
import time
import random
import requests
from hashlib import md5
from pyquery import PyQuery as pq
user1 = 'swishersweets'
user2 = 'backwoods_cigars'
url_base = 'https://www.instagram.com/'
uri = 'https://www.instagram.com/graphql/query/?query_hash=a5164aed103f24b03e7b7747a2d94e3c&variables=%7B%22id%22%3A%22{user_id}%22%2C%22first%22%3A12%2C%22after%22%3A%22{cursor}%22%7D'

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    'cookie': 'mid=YHGMNwALAAHqrRyIMv9ISIub7nPi; ig_did=408DB146-D8D0-45DC-8D17-CE0BC2EA2760; ig_nrcb=1; csrftoken=bkmUlyvX25nCoc3Np83lykpjWyCvXjX0; ds_user_id=46991241491; sessionid=46991241491%3AChmWh0yMCZCCd7%3A10; rur=FTW'
}

proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}#change to your own proxies

def transform_time(dt):
    time_array = time.strptime(dt, "%Y-%m-%d %H:%M:%S")
    timestamp = time.mktime(time_array)
    return timestamp

start_time = transform_time('2020-12-31 23:59:59')
end_time = transform_time('2018-01-01 00:00:00')

def get_html(url):
    try:
        response = requests.get(url, headers=headers, proxies=proxies)
        if response.status_code == 200:
            return response.text
        else:
            print('Request webpage source code error, error status code：', response.status_code)
    except Exception as e:
        print(e)
        return None


def get_json(url):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print('Request webpage json error, error status code：', response.status_code)
    except Exception as e:
        print(e)
        time.sleep(60 + float(random.randint(1, 4000)) / 100)
        return get_json(url)


def get_content(url):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.content
        else:
            print('Request photo binary stream error, error status code：', response.status_code)
    except Exception as e:
        print(e)
        return None

def get_urls(html):
    urls = []
    comment_dic = {}
    text_dic = {}
    user_id = re.findall('"profilePage_([0-9]+)"', html, re.S)[0]
    print('user_id：' + user_id)
    doc = pq(html)
    items = doc('script[type="text/javascript"]').items()
    for item in items:
        if item.text().strip().startswith('window._sharedData'):
            js_data = json.loads(item.text()[21:-1], encoding='utf-8')
            edges = js_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"]
            page_info = js_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"][
                'page_info']
            cursor = page_info['end_cursor']
            flag = page_info['has_next_page']
            for edge in edges:
                tmp_url = None
                # if edge['node']['taken_at_timestamp'] < start_time or edge['node']['taken_at_timestamp'] > end_time:
                #     continue

                if edge['node']['display_url']:
                    display_url = edge['node']['display_url']
                    print(display_url)
                    urls.append(display_url)
                    if display_url not in comment_dic.keys():
                        comment_dic[display_url] = []
                    
                    if display_url not in text_dic.keys():
                        text_dic[display_url] = []
                    tmp_url = display_url

                if tmp_url != None:
                    if edge['node']['edge_media_to_caption']['edges']:
                        text_dic[tmp_url].append(edge['node']['edge_media_to_caption']['edges'][0]['node']['text'])

    while flag:
        url = uri.format(user_id=user_id, cursor=cursor)
        js_data = get_json(url)
        infos = js_data['data']['user']['edge_owner_to_timeline_media']['edges']
        cursor = js_data['data']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']
        flag = js_data['data']['user']['edge_owner_to_timeline_media']['page_info']['has_next_page']
        
        for info in infos:
            tmp_url = None
            # if info['node']['taken_at_timestamp'] < start_time or info['node']['taken_at_timestamp'] > end_time:
            #         continue
            if info['node']['is_video']:
                video_url = info['node']['video_url']
                if video_url:
                    urls.append(video_url)
                    if video_url not in comment_dic.keys():
                        comment_dic[video_url] = []
                    
                    if video_url not in text_dic.keys():
                        text_dic[video_url] = []
                    tmp_url = video_url
            else:
                if info['node']['display_url']:
                    display_url = info['node']['display_url']
                    urls.append(display_url)
                    if display_url not in comment_dic.keys():
                        comment_dic[display_url] = []
                    
                    if display_url not in text_dic.keys():
                        text_dic[display_url] = []
                    tmp_url = display_url
            
            if tmp_url != None:
                if info['node']['edge_media_to_caption']['edges'][0]['node']['text']:
                    text_dic[tmp_url].append(info['node']['edge_media_to_caption']['edges'][0]['node']['text'])
                
                if info['node']['edge_media_to_comment']:
                    size = len(info['node']['edge_media_to_comment']['edges'])
                    for i in range(size):
                        comment = info['node']['edge_media_to_comment']['edges'][i]['node']
                        comment_dic[tmp_url].append(comment['text'])

        time.sleep(1)
    return urls, text_dic, comment_dic


def main(user):
    url = url_base + user + '/'
    html = get_html(url)
    urls, text_dic, comment_dic = get_urls(html)
    idx = 0
    if not os.path.exists('download_files/'+user):
        os.mkdir('download_files/'+user)
        os.mkdir('download_files/'+user+'/posts')
        os.mkdir('download_files/'+user+'/comments')
        os.mkdir('download_files/'+user+'/photos')

    for post_url, text in text_dic.items():
        file_path = r'download_files\{1}\posts\{0}.txt'.format(idx, user)
        idx += 1
        with open(file_path, 'w', encoding='utf8') as f:
            for single_text in text:
                f.write(single_text+'\n')

    idx = 0
    for post_url, text in comment_dic.items():
        file_path = r'download_files\{1}\comments\{0}.txt'.format(idx, user)
        idx += 1
        with open(file_path, 'w', encoding='utf8') as f:
            for single_text in text:
                f.write(single_text+'\n')

    dispatch = r'.\download_files\{0}\photos'.format(user)
    if not os.path.exists(dispatch):
        os.mkdir(dispatch)
    for i in range(len(urls)):
        print('\nnow downloading {0} pics： '.format(i) + urls[i], ' remaining {0} pics'.format(len(urls) - i - 1))
        try:
            content = get_content(urls[i])
            endw = 'mp4' if r'mp4?_nc_ht=scontent' in urls[i] else 'jpg'
            file_path = r'.\download_files\{0}\photos\{1}.{2}'.format(user, i, endw)
            if not os.path.exists(file_path):
                with open(file_path, 'wb') as f:
                    print('pic {0} done： '.format(i) + urls[i])
                    f.write(content)
                    f.close()
            else:
                print('pic {0}already done'.format(i))
        except Exception as e:
            print(e)
            print('video or pic download failed')


if __name__ == '__main__':
    start = time.time()
    main(user1)
    main(user2)
    print('Complete!!!!!!!!!!')
    end = time.time()
    spend = end - start
    hour = spend // 3600
    minu = (spend - 3600 * hour) // 60
    sec = spend - 3600 * hour - 60 * minu
    print(f'cost{hour}hr{minu}min{sec}sec')