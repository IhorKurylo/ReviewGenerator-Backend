import os
import os.path
import re
import pprint
import sys
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize


def clean(txt: str):
    keep_characters = set(
        'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-@ ,\'"().!?\n\r ')
    new_text = ''.join(ch for ch in txt if ch in keep_characters)
    return new_text


with open("./pinecone.txt", 'r') as fin:
    FileinA = (fin.read())
    FileinA = clean(FileinA)
    FileinB = nltk.sent_tokenize(FileinA)
    print('2 Tokenized File')
    print(FileinB)
    print(' ')
    # create basename by deleting the file name suffix
    sent_seen = set()  # holds lines already seen
    for sent in FileinB:
        if sent not in sent_seen:
            sent = sent.strip()
            sent_seen.add(sent)
            print(sent)
            # print(sent_seen, '\n')
