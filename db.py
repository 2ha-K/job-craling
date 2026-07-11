from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

db = None

def get_db():
    global db
    if db is None:
        client = MongoClient(
            os.getenv("MONGO_URL"),
        )
        db = client[os.getenv("MONGO_DB")]
        return db
    else:
        return db

def get_collection(collection):
    database = get_db()
    collection = database[collection]
    return collection

if __name__ == "__main__":
    collection = get_collection("posts")
    # collection.create_index(
    #     "post_key",
    #     unique=True
    # )
    collection.delete_many({})
    print("完成")