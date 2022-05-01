from pymongo import MongoClient
import pymongo

# mongo db as a class
class database:
    def __init__(self) -> None:
        self.db = None
    def connect_db(self):
        client = pymongo.MongoClient(
                "mongodb+srv://BoyuChen:2000118tten@cluster0.9epq9.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        self.db = client['BillSplitter']

    def insert_data(self, collectionName, data):
        self.db.get_collection(collectionName).insert_one(data)