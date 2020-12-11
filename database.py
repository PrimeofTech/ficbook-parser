import os

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate('serviceAccount.json')
firebase_admin.initialize_app(cred)
db = firestore.client()


class Sessions:
    def __init__(self):
        global db
        self.collection = db.collection('sessions')

    def __setitem__(self, key, value):
        self.collection.document(key).set(value, merge=True)

    def __getitem__(self, item):
        doc = self.collection.document(item).get()
        if doc.exists:
            return doc.to_dict()
        else:
            return False


if __name__ == '__main__':
    s = Sessions()
    c = s['blalasdmasod90q3n']
    print('original ', c)
    c['a'] = 3
    print('A basic ', c)
    print('A get ', s['blalasdmasod90q3n'])
    c['a'] = 4
    s['blalasdmasod90q3n'] = c
    print('B basic ', c)
    print('B get ', s['blalasdmasod90q3n'])

