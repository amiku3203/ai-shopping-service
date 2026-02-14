from bson import ObjectId
from datetime import datetime

def serialize_mongo_obj(obj):
    """
    Recursively convert ObjectId to str for JSON serialization.
    """
    if isinstance(obj, list):
        return [serialize_mongo_obj(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: serialize_mongo_obj(v) for k, v in obj.items()}
    elif isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj
