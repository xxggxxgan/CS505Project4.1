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
# user2 = 'backwoods_cigars'

url_base = 'https://www.instagram.com/'
uri = 'https://www.instagram.com/graphql/query/?query_hash=a5164aed103f24b03e7b7747a2d94e3c&variables=%7B%22id%22%3A%22{user_id}%22%2C%22first%22%3A12%2C%22after%22%3A%22{cursor}%22%7D'
comment_uri = 'https://www.instagram.com/graphql/query/?query_hash=cf28bf5eb45d62d4dc8e77cdb99d750d&variables=%7B%22shortcode%22%3A%22CNi0zYsjGrw%22%2C%22child_comment_count%22%3A3%2C%22fetch_comment_count%22%3A40%2C%22parent_comment_count%22%3A24%2C%22has_threaded_comments%22%3Atrue%7D'

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    'cookie': 'mid=YHGMNwALAAHqrRyIMv9ISIub7nPi; ig_did=408DB146-D8D0-45DC-8D17-CE0BC2EA2760; ig_nrcb=1; csrftoken=bkmUlyvX25nCoc3Np83lykpjWyCvXjX0; ds_user_id=46991241491; sessionid=46991241491%3AChmWh0yMCZCCd7%3A10; rur=FTW'
}

proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}

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
        # headers['user-agent'] = headers_choice[random.randint(0, len(headers_choice))]
        response = requests.get(url, headers=headers, proxies=proxies)
        if response.status_code == 200:
            return response.text
        else:
            print('Failed to get html, error code:', response.status_code)
    except Exception as e:
        print(e)
        return None

def get_json(url):
    try:
        # headers['user-agent'] = headers_choice[random.randint(0, len(headers_choice))]
        response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print('Failed to get json, error code:', response.status_code)
            print('Sleep a time')
            time.sleep(60 + float(random.randint(1, 4000)) / 100)
            return get_json(url)

    except Exception as e:
        print(e)
        print('Sleep a time')
        time.sleep(60 + float(random.randint(1, 4000)) / 100)
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
comment_pattern = r'"text": "(.*?)"'

def get_comment(edge, comment_dic, url, user_id):
    flag = edge['page_info']['has_next_page']
    cursor = edge['page_info']['end_cursor']
    size = len(edge['edges'])

    for i in range(size):
        comment = edge['edges'][i]['node']
        comment_dic[url].append(comment['text'])

    # while flag:
    #     tmpurl = uri.format(user_id=user_id, cursor=cursor)
    #     print(tmpurl)
    #     js_data = get_json(tmpurl)
    #     flag = js_data['data']['user'][media_kw]['page_info']['has_next_page']
    #     cursor = js_data['data']['user'][media_kw]['page_info']['end_cursor']
    #     js_data_text = json.dumps(js_data)
    #     text_all = re.findall('{"text": (.*?)}', js_data_text)
    #     if len(text_all) > 0:
    #         comment_dic[url].extend(text_all)
    #     # print(text_all)
    #     # sys.exit(1)
    #     time.sleep(random.randint(0, 3))

def iterate_edges(edges, urls, comment_dic, text_dic, user_id):
    for edge in edges:
        tmp_url = None
        # print(edge['node'][timestamp_kw])
        # time control, if current time > end_time, continue
        if edge['node'][timestamp_kw] > end_time:
            continue
        # if current time < start_time, stop request
        elif edge['node'][timestamp_kw] < start_time:
            return False
        
        print(transform_timestamp(edge['node'][timestamp_kw]))
        # print('time:', transform_timestamp(edge['node'][timestamp_kw]))
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

            # if comment_kw in edge['node'].keys():
            #     response = requests.get(comment_uri, headers=headers, proxies=proxies, timeout=10, \
            #                              params={'shortcode':shortcode, 'child_comment_count':'3', \
            #                                      'fetch_comment_count':'40', 'parent_comment_count':'24',\
            #                                      'has_threaded_comments':'true'})

            #     print(re.findall('"text":"(.*?)"', response.text))

            #     size = len(edge['node'][comment_kw]['edges'])
            #     for i in range(size):
            #         comment = edge['node'][comment_kw]['edges'][i]['node']
            #         comment_dic[tmp_url].append(comment['text'])
                # try:
                #     get_comment(edge['node'][comment_kw], comment_dic, tmp_url, user_id)
                # except:
                #     pass
                
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
    # for post_url, text in text_dic.items():
    #     file_path = r'download_files\{1}\posts\{0}.txt'.format(idx, user)
    #     idx += 1
    #     with open(file_path, 'w', encoding='utf8') as f:
    #         for single_text in text:
    #             f.write(single_text+'\n')
    
    # idx = 0
    # for post_url, text in comment_dic.items():
    #     file_path = r'download_files\{1}\comments\{0}.txt'.format(idx, user)
    #     idx += 1
    #     with open(file_path, 'w', encoding='utf8') as f:
    #         for single_text in text:
    #             f.write(single_text+'\n')
    
    for i in range(len(urls)):
        print('Downloading number.{0} media: '.format(i)+urls[i], ' Remaining {0} medias'.format(len(urls)-i-1))
        try:
            content = get_content(urls[i])
            endw = 'mp4' if r'mp4?_nc_ht=scontent' in urls[i] else 'jpg'
            file_path = r'\download_files\{0}\photos\{1}.{2}'.format(user, i, endw)
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
    main(user1)
    # main(user2)
    print('Complete!!!!!!!!!!')
    end = time.time()
    spend = end - start
    hour = spend // 3600
    minu = (spend - 3600 * hour) // 60
    sec = spend - 3600 * hour - 60 * minu
    print(f'Spend {hour}h {minu}m {sec}s')