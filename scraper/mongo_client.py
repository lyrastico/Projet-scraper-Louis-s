from pymongo import MongoClient

def get_mongo_collection(collection_name="matchs"):
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["liquipedia"]
        return db[collection_name]
    except Exception as e:
        print(f"Erreur de connexion à MongoDB : {e}")
        return None