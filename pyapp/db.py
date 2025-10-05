from pymongo import MongoClient
from .config import settings

client = MongoClient(settings.MONGODB_URI)
default_db = client.get_default_database()
db = default_db if default_db is not None else client["justdial_project1"]

users = db["users"]
videos = db["videos"]
plugin_settings = db["plugin_settings"]
projects = db["projects"]
tasks = db["tasks"]