from pymongo import MongoClient

def get_mongo_collection():
    client = MongoClient("mongodb://localhost:27017/")
    db = client['liquipedia']
    collection = db['teams']
    return collection
