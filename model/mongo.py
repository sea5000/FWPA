import os
from pymongo import MongoClient

_client = None
_db = None


def get_db():
    global _client, _db
    if _db is not None:
        return _db
    uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
    db_name = os.environ.get('MONGO_DB', 'bookme')
    _client = MongoClient(uri)
    _db = _client[db_name]
    return _db
