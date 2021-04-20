import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import bert
import pandas as pd
import sys

def get_model(model_path, max_seq_length):
    labse_layer = hub.KerasLayer(model_path, trainable=True)

    # Define input.
    input_word_ids = tf.keras.layers.Input(shape=(max_seq_length,), dtype=tf.int32,
                                            name="input_word_ids")
    input_mask = tf.keras.layers.Input(shape=(max_seq_length,), dtype=tf.int32,
                                        name="input_mask")
    segment_ids = tf.keras.layers.Input(shape=(max_seq_length,), dtype=tf.int32,
                                        name="segment_ids")

    # LaBSE layer.
    pooled_output,  _ = labse_layer([input_word_ids, input_mask, segment_ids])

    # The embedding is l2 normalized.
    pooled_output = tf.keras.layers.Lambda(
        lambda x: tf.nn.l2_normalize(x, axis=1))(pooled_output)

    # Define model.
    return tf.keras.Model(
            inputs=[input_word_ids, input_mask, segment_ids],
            outputs=pooled_output), labse_layer

max_seq_length = 256
labse_model, labse_layer = get_model(model_path="LaBSE_1", max_seq_length=max_seq_length)

vocab_file = labse_layer.resolved_object.vocab_file.asset_path.numpy()
do_lower_case = labse_layer.resolved_object.do_lower_case.numpy()
tokenizer = bert.bert_tokenization.FullTokenizer(vocab_file, do_lower_case)

def create_input(input_strings, tokenizer, max_seq_length):
    input_ids_all, input_mask_all, segment_ids_all = [], [], []
    for input_string in input_strings:
        # Tokenize input.
        input_tokens = ["[CLS]"] + tokenizer.tokenize(input_string) + ["[SEP]"]
        input_ids = tokenizer.convert_tokens_to_ids(input_tokens)
        sequence_length = min(len(input_ids), max_seq_length)

        # Padding or truncation.
        if len(input_ids) >= max_seq_length:
            input_ids = input_ids[:max_seq_length]
        else:
            input_ids = input_ids + [0] * (max_seq_length - len(input_ids))

            input_mask = [1] * sequence_length + [0] * (max_seq_length - sequence_length)

            input_ids_all.append(input_ids)
            input_mask_all.append(input_mask)
            segment_ids_all.append([0] * max_seq_length)

    return np.array(input_ids_all), np.array(input_mask_all), np.array(segment_ids_all)

def encode(input_text):
    input_ids, input_mask, segment_ids = create_input(input_text, tokenizer, max_seq_length)
    return labse_model([input_ids, input_mask, segment_ids])

with open('warning.txt', 'r') as f:
    WARNING_SENTENCES_SET = f.read().strip().split('\n')

WARNING_SENTENCES_EMBEDDINGS = encode(WARNING_SENTENCES_SET)

THRESHOLD = 0.5
def encode_data(df, kw):
    sentences = df[kw]
    sentences_embedding = encode(sentences)
    return sentences_embedding

def annodate_data(simmularity_matrix):
    labels = []
    n, m = simmularity_matrix.shape
    print(n)
    for i in range(n):
        flag = False
        for j in range(m):
            if simmularity_matrix[i][j] > THRESHOLD:
                labels.append('True')
                flag = True
                break
        if flag == False:
            labels.append('False')
    print(len(labels))
    return labels

import string
def preprocess_text(df, kw):
    df[kw] = df[kw].apply(lambda x: str(x))
    punction = string.punctuation
    for p in punction:
        df[kw] = df[kw].apply(lambda x: x.replace(p, ''))

def annotate_post():
    POSTS_DATA_PATH = 'download_files/posts.csv'
    post_df = pd.read_csv(POSTS_DATA_PATH)
    post_df = post_df.dropna()
    preprocess_text(post_df, 'text')
    post_df = post_df[post_df.text != ''].reset_index()
    print('post df shape', post_df.shape)
    post_embedding = encode_data(post_df, 'text')
    print('post df embedding shape', post_embedding.shape)
    post_simu_matrix = np.matmul(post_embedding, np.transpose(WARNING_SENTENCES_EMBEDDINGS))
    post_label = annodate_data(post_simu_matrix)
    post_df['tobacco_warning'] = pd.Series(post_label)
    post_df.to_csv('download_files/posts_final_v0.csv', index=False)
    print('annotate post done')

def annotate_comment():
    COMMENT_DATA_PATH = 'download_files/comment.csv'
    comment_df = pd.read_csv(COMMENT_DATA_PATH)
    comment_df = comment_df.dropna()
    preprocess_text(comment_df, 'text')
    comment_df = comment_df[comment_df.text != ''].reset_index()
    batch = 1000
    label = []
    num_batch = int(comment_df.shape[0] / batch)
    for idx in range(num_batch):
        if idx*batch+batch < comment_df.shape[0]:
            tmp_text = comment_df.iloc[idx*batch:idx*batch+batch, :]
        else:
            tmp_text = comment_df.iloc[idx*batch:-1, :]
        tmp_text_embedding = encode_data(tmp_text, 'text')
        assert(tmp_text_embedding.shape[0] == tmp_text.shape[0])
        comment_simu_matrix = np.matmul(tmp_text_embedding, np.transpose(WARNING_SENTENCES_EMBEDDINGS))
        comment_label = annodate_data(comment_simu_matrix)
        label.extend(comment_label)
    
    comment_df['tobacco_warning'] = pd.Series(label)
    comment_df.to_csv('download_files/comment_final_v0.csv', index=False)
    print('annotate comment done')

annotate_post()
annotate_comment()