from pymongo import MongoClient
from config import MONGO_URI, MONGO_DB_NAME

client = MongoClient(MONGO_URI)
mongo_db = client[MONGO_DB_NAME]

leave_requests = mongo_db["leave_requests"]
overtime_requests = mongo_db["overtime_requests"]
performance_reviews = mongo_db["performance_reviews"]
