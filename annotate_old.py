import pandas as pd
import os
import re

exp_sponsorship_tag = ['#sponsored', '#ad', '#paid']
amb_sponsorship_tag = ['#thanks', '#sp', '#spon', '#ambassador', '#collab']

user1 = 'swishersweets'
user2 = 'backwoods_cigars'

pattern = r"#[a-zA-Z0-9]+\s*"
def contain_tag(text, tag_set):
    for tag in tag_set:
        if tag in text:
            return True
    
    return False

def remove_tag(text):
    text_ = re.sub(pattern, "", text)
    return text_

df = {'id': [], 'text': [], 'exp_tag': [], 'amb_tag': []}
for user in [user1, user2]:
    for path, dir_list, file_list in os.walk('download_files/%s/comments' % user):
        for file_name in file_list:
            id_ = file_name.split('.')[0]
            with open(os.path.join(path, file_name), 'r', encoding='utf8') as f:
                f_content = f.read().strip().split('\n')
                for text in f_content:
                    df['text'].append(remove_tag(text))
                    df['exp_tag'].append(contain_tag(text, exp_sponsorship_tag))
                    df['amb_tag'].append(contain_tag(text, amb_sponsorship_tag))
                    df['id'].append(user+id_)

df = pd.DataFrame(df)
df.to_csv('download_files/comment.csv')

df = {'id': [], 'text': [], 'exp_tag': [], 'amb_tag': []}
for user in [user1, user2]:
    for path, dir_list, file_list in os.walk('download_files/%s/posts' % user):
        for file_name in file_list:
            id_ = file_name.split('.')[0]
            with open(os.path.join(path, file_name), 'r', encoding='utf8') as f:
                text = f.read().replace('\n', ' ').strip()
                df['text'].append(remove_tag(text))
                df['exp_tag'].append(contain_tag(text, exp_sponsorship_tag))
                df['amb_tag'].append(contain_tag(text, amb_sponsorship_tag))
                df['id'].append(user+' '+id_)

df = pd.DataFrame(df)
df.to_csv('download_files/posts.csv')