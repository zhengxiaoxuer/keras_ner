#! -*- coding:utf-8 -*-

import json
import numpy as np
import pandas as pd
from random import choice
from keras_bert import load_trained_model_from_checkpoint, Tokenizer
from keras_contrib.layers import CRF
import re, os
import codecs
import proccess_data


config_path = '/home/zx/Downloads/chinese_L-12_H-768_A-12/bert_config.json'
checkpoint_path = '/home/zx/Downloads/chinese_L-12_H-768_A-12/bert_model.ckpt'
dict_path = '/home/zx/Downloads/chinese_L-12_H-768_A-12/vocab.txt'
chunk_tags = ['[CLS]','O', 'B-PAR', 'I-PAR','B-EQU', 'I-EQU', 'B-ETP', 'I-ETP','B-CHE', 'I-CHE', 'B-ORG', 'I-ORG','[SEP]']

token_dict = {}

with codecs.open(dict_path, 'r', 'utf8') as reader:
    for line in reader:
        token = line.strip()
        token_dict[token] = len(token_dict)


class OurTokenizer(Tokenizer):
    def _tokenize(self, text):
        R = []
        for c in text:
            if c in self._token_dict:
                R.append(c)
            elif self._is_space(c):
                R.append('[unused1]') # space类用未经训练的[unused1]表示
            else:
                R.append('[UNK]') # 剩余的字符是[UNK]
        return R

tokenizer = OurTokenizer(token_dict)

data = proccess_data.load_data()
# neg = pd.read_excel('neg.xls', header=None)
# pos = pd.read_excel('pos.xls', header=None)

# data = []

# for d in neg[0]:
#     data.append((d, 0))

# for d in pos[0]:
#     data.append((d, 1))


# 按照9:1的比例划分训练集和验证集
random_order = range(len(data))
np.random.shuffle([random_order])
train_data = [data[j] for i, j in enumerate(random_order) if i % 10 != 0]
valid_data = [data[j] for i, j in enumerate(random_order) if i % 10 == 0]


def seq_padding(X, padding=0):
    L = [len(x) for x in X]
    ML = max(L)
    return np.array([
        np.concatenate([x, [padding] * (ML - len(x))]) if len(x) < ML else x for x in X
    ])

# x = [[w[0].lower() for w in s] for s in data]
# y_chunk = [[chunk_tags.index(w[1]) for w in s] for s in data]
class data_generator:
    def __init__(self, data, batch_size=32):
        self.data = data
        self.batch_size = batch_size
        self.steps = len(self.data) // self.batch_size
        if len(self.data) % self.batch_size != 0:
            self.steps += 1
    def __len__(self):
        return self.steps
    def __iter__(self):
        while True:
            idxs = range(len(self.data))
            np.random.shuffle(idxs)
            X1, X2, Y = [], [], []
            for i in idxs:
                
                d = self.data[i]#句子#data[i]=[[字,tags]，[字],...]
                dt=[x[0] for x in d]  #句子[zi,zi,zi...]
                text = dt[0]
                x1, x2 = tokenizer.encode(first=text)
                y_chunk =[x[1] for x in d]
                y = [chunk_tags.index(t) for t in y_chunk] 
                y.insert(0,'[CLS]')#list添加元素
                y.append('[SEP]')
                y = np.expand_dims(y, 1)
                X1.append(x1)
                X2.append(x2)
                Y.append(y)
                if len(X1) == self.batch_size or i == idxs[-1]:
                    X1 = seq_padding(X1)
                    X2 = seq_padding(X2)
                    Y = seq_padding(Y)
                    yield [X1, X2], Y
                    [X1, X2, Y] = [], [], []


from keras.layers import *
from keras.models import Model
import keras.backend as K
from keras.optimizers import Adam


bert_model = load_trained_model_from_checkpoint(config_path, checkpoint_path, seq_len=None)

for l in bert_model.layers:
    l.trainable = True

# x1_in = Input(shape=(None,))
# x2_in = Input(shape=(None,))
# x = bert_model([x1_in, x2_in])
# p = Dense(len(chunk_tags), activation='sigmoid')(x)
# crf = CRF(len(chunk_tags), sparse_target=True)
# output = crf(p)

x1_in = Input(shape=(None,))
x2_in = Input(shape=(None,))
x = bert_model([x1_in, x2_in])
p = Dense(128, activation='sigmoid')(x)
crf = CRF(len(chunk_tags), sparse_target=True)
output = crf(p)
model = Model([x1_in, x2_in], output)
model.compile(
    loss=crf.loss_function,
    optimizer=Adam(1e-5),# 用足够小的学习率
    metrics=[crf.accuracy]
)
# model.compile(
#     loss='binary_crossentropy',
#     optimizer=Adam(1e-5), # 用足够小的学习率
#     metrics=['accuracy']
# )
model.summary()


train_D = data_generator(train_data)
valid_D = data_generator(valid_data)

model.fit_generator(
    train_D.__iter__(),
    steps_per_epoch=len(train_D),
    epochs=5,
    validation_data=valid_D.__iter__(),
    validation_steps=len(valid_D)
)

model.save_weights('m1.h5')