from pymongo import MongoClient
from config import settings

client = MongoClient(settings.MONGO_URL)

db = client[settings.DATABASE_NAME]

products_collection = db["products"]
