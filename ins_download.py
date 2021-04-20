import os
import re
import sys
import json
import time
import random
import requests
import shutil
from pyquery import PyQuery as pq

user1 = 'swishersweets'
user2 = 'backwoods_cigars'

url_base = 'https://www.instagram.com/'
uri = 'https://www.instagram.com/graphql/query/?query_hash=a5164aed103f24b03e7b7747a2d94e3c&variables=%7B%22id%22%3A%22{user_id}%22%2C%22first%22%3A12%2C%22after%22%3A%22{cursor}%22%7D'
comment_uri = 'https://www.instagram.com/graphql/query/?query_hash=cf28bf5eb45d62d4dc8e77cdb99d750d&variables=%7B%22shortcode%22%3A%22{shortcode}%22%2C%22child_comment_count%22%3A3%2C%22fetch_comment_count%22%3A40%2C%22parent_comment_count%22%3A24%2C%22has_threaded_comments%22%3Atrue%7D'

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
    'cookie': 'mid=YGchywAEAAHu0Qt_SlecManLweTy; ig_did=AEF1B10C-4DA6-438C-B627-A50F5EDA2C9B; ig_nrcb=1; csrftoken=RZ6Z5Ir0qsSwQeX2YTesPOlvGi84M7gE; ds_user_id=1379532750; sessionid=1379532750%3Aeh7ZuUb20mTHDJ%3A14; rur=ASH'
}

#proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}

def transform_time(dt):
    time_array = time.strptime(dt, "%Y-%m-%d %H:%M:%S")
    timestamp = time.mktime(time_array)
    return timestamp

def transform_timestamp(timestamp):
    time_local = time.localtime(timestamp)
    dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
    return dt

end_time = transform_time('2020-12-31 23:59:59')
# end_time = transform_time('2021-04-15 23:59:59')
start_time = transform_time('2018-01-01 00:00:00')
# start_time = transform_time('2021-03-14 00:00:00')

def get_html(url):
    try:
        response = requests.get(url, headers=headers)#proxies=proxies
        if response.status_code == 200:
            return response.text
        else:
            print('Failed to get html, error code:', response.status_code)
    except Exception as e:
        print(e)
        return None

def get_json(url):
    try:
        response = requests.get(url, headers=headers, timeout=10)#, proxies=proxies
        if response.status_code == 200:
            return response.json()
        else:
            print('Failed to get json, error code:', response.status_code)
            print('Sleep a time')
            time.sleep(120 + float(random.randint(1, 4000)) / 100)
            return get_json(url)

    except Exception as e:
        print(e)
        print('Sleep a time')
        time.sleep(120 + float(random.randint(1, 4000)) / 100)
        return get_json(url)

def get_content(url):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.content
        else:
            print('Failed to download media, error code:', response.status_code)
    except Exception as e:
        print(e)
        return None

user_pattern = 'profilePage_([0-9]+)'
js_pattern = 'script[type="text/javascript"]'
share_data_pattern = 'window._sharedData'
media_kw = 'edge_owner_to_timeline_media'
caption_kw = 'edge_media_to_caption'
timestamp_kw = 'taken_at_timestamp'
comment_kw = 'edge_media_to_comment'

def iterate_edges(edges, urls, comment_dic, text_dic, user_id):
    for edge in edges:
        tmp_url = None

        if edge['node'][timestamp_kw] > end_time:
            continue

        elif edge['node'][timestamp_kw] < start_time:
            return False
        
        print(transform_timestamp(edge['node'][timestamp_kw]))
        if edge['node']['is_video']:
            video_url = edge['node']['video_url']
            if video_url:
                urls.append(video_url)
                if video_url not in comment_dic.keys():
                    comment_dic[video_url] = []
                
                if video_url not in text_dic.keys():
                    text_dic[video_url] = []
                tmp_url = video_url

        else:
            display_url = edge['node']['display_url']
            if display_url:
                urls.append(display_url)
                if display_url not in comment_dic.keys():
                    comment_dic[display_url] = []
                
                if display_url not in text_dic.keys():
                    text_dic[display_url] = []
                tmp_url = display_url

        shortcode = edge['node']['shortcode']
        if tmp_url != None:
            if caption_kw in edge['node'].keys():
                try:
                    text_dic[tmp_url].append(edge['node'][caption_kw]['edges'][0]['node']['text'])
                except:
                    pass

            if comment_kw in edge['node'].keys():
                comment_url = comment_uri.format(shortcode=shortcode)
                comment_json = get_json(comment_url)
                comments = comment_json['data']['shortcode_media']['edge_media_to_parent_comment']['edges']

                comment_dic[tmp_url].extend(re.findall("'text': '(.*?)'", str(comments)))
                time.sleep(3)
    
    return True

def get_urls(html):
    urls = []
    comment_dic = {}
    text_dic = {}
    flag = None
    user_id = re.findall(user_pattern, html, re.S)[0]
    print('user_id:' + user_id)

    doc = pq(html)
    items = doc(js_pattern).items()
    for item in items:
        if item.text().strip().startswith(share_data_pattern):
            js_data = json.loads(item.text()[21:-1], encoding='utf8')
            media = js_data['entry_data']['ProfilePage'][0]['graphql']['user'][media_kw]
            edges = media['edges']
            page_info = media['page_info']
            cursor = page_info['end_cursor']
            flag = page_info['has_next_page']
            
            # originally, there will be 12 display url
            status = iterate_edges(edges, urls, comment_dic, text_dic, user_id)
            if status == False:
                return urls, comment_dic, text_dic
        
        # look up not display url
        while flag:
            url = uri.format(user_id=user_id, cursor=cursor)
            js_data = get_json(url)
            media = js_data['data']['user'][media_kw]
            edges = media['edges']
            page_info = media['page_info']
            cursor = page_info['end_cursor']
            flag = page_info['has_next_page']

            status = iterate_edges(edges, urls, comment_dic, text_dic, user_id)
            if status == False:
                return urls, comment_dic, text_dic
            
            time.sleep(3)
    return urls, comment_dic, text_dic

def main(user):
    url = url_base + user + '/'
    html = get_html(url)
    urls, comment_dic, text_dic = get_urls(html)

    if not os.path.exists('download_files/'):
        os.mkdir('download_files')
    
    if os.path.exists('download_files/' + user):
        shutil.rmtree('download_files/' + user)
    
    os.mkdir('download_files/'+user)
    os.mkdir('download_files/'+user+'/posts')
    os.mkdir('download_files/'+user+'/comments')
    os.mkdir('download_files/'+user+'/photos')

    idx = 0
    for post_url, text in text_dic.items():
        file_path = './download_files/{1}/posts/{0}.txt'.format(idx, user)
        idx += 1
        with open(file_path, 'w', encoding='utf8') as f:
            for single_text in text:
                f.write(single_text+'\n')
    
    idx = 0
    for post_url, text in comment_dic.items():
        file_path = './download_files/{1}/comments/{0}.txt'.format(idx, user)
        idx += 1
        with open(file_path, 'w', encoding='utf8') as f:
            for single_text in text:
                f.write(single_text+'\n')

    for i in range(len(urls)):
        print('Downloading number.{0} media: '.format(i)+urls[i], ' Remaining {0} medias'.format(len(urls)-i-1))
        try:
            content = get_content(urls[i])
            endw = 'mp4' if r'mp4?_nc_ht=scontent' in urls[i] else 'jpg'
            file_path = './download_files/{0}/photos/{1}.{2}'.format(user, i, endw)
            if not os.path.exists(file_path):
                with open(file_path, 'wb') as f:
                    print('Download number.{0} media done'.format(i))
                    f.write(content)
                    f.close()
            else:
                print('Number.{0} media already downloaded'.format(i))
        except Exception as e:
            print(e)
            print('Download number.{0} media failed'.format(i))

if __name__ == '__main__':
    start = time.time()
    # print('user:', user1)
    main(user1)
    main(user2)
    print('Complete!!!!!!!!!!')
    end = time.time()
    spend = end - start
    hour = spend // 3600
    minu = (spend - 3600 * hour) // 60
    sec = spend - 3600 * hour - 60 * minu
    print(f'Spend {hour}h {minu}m {sec}s')