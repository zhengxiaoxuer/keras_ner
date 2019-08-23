import numpy
from collections import Counter
from keras.preprocessing.sequence import pad_sequences
import pickle
import platform
import codecs

chunk_tags = ['[CLS]','O', 'B-PAR', 'I-PAR','B-EQU', 'I-EQU', 'B-ETP', 'I-ETP','B-CHE', 'I-CHE', 'B-ORG', 'I-ORG','[SEP]']
def load_data():
    ##data=[[[字，tags],[字，tags],[字，tags],..],[[],[]...],........]]]
    data = _parse_data(open('/home/zx/aalearning/bert_in_keras/NERdata/train+test.txt', 'rb'))
    return data


def _parse_data(fh):
    #  in windows the new line is '\r\n\r\n' the space is '\r\n' . so if you use windows system,
    #  you have to use recorsponding instructions

    if platform.system() == 'Windows':
        split_text = '\r\n'
    else:
        split_text = '\n'

    string = fh.read().decode('utf-8')#读整篇文档为一个字符串
    #data=[[[字，tags],[字，tags],[字，tags],..],[[],[]...],........]]]
    data = [[row.split() for row in sample.split(split_text)] for#row 行
            sample in#sample段落
            string.strip().split(split_text + split_text)]
    fh.close()
    # x = [[w[0].lower() for w in s] for s in data]
    # y_chunk = [[chunk_tags.index(w[1]) for w in s] for s in data]
    return data

