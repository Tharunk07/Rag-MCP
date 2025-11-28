from config import MONGO_DB, MONGO_DB_URI
from .mongo_client import get_db
from datetime import datetime, timezone

MONGO_CONNECTION = MONGO_DB_URI
KAPAI_DB = MONGO_DB

MONGO_CHAT_STORAGE_COLLECTION = "chat_storage"

def get_collection(collection_name):

    return get_db()[collection_name]


async def insert_one_data(collection_name, data):

    return await get_collection(collection_name).insert_one(data)

async def insert_many_data(collection_name, data):

    return await get_collection(collection_name).insert_many(data)

async def find_data(collection_name, find_query):

    cursor = get_collection(collection_name).find(find_query)
    return await cursor.to_list(length=None)

async def update_data(collection_name, find_query, update_query):

    return await get_collection(collection_name).update_many(find_query, update_query)

async def find_one_data(collection_name, find_query, sort_by="created_at", skip_by=0):

    cursor = (
        get_collection(collection_name)
        .find(find_query)
        .sort(sort_by, -1)
        .skip(skip_by)
        .limit(1)
    )
    docs = await cursor.to_list(length=1)
    return docs[0] if docs else None


async def update_one_data(collection_name, find_query, update_query, sort=[("created_at", -1)]):

    return await get_collection(collection_name).find_one_and_update(
        filter=find_query,
        update=update_query,
        sort=sort,
    )

async def claude_usage_data(date_str):

    collection = get_collection(MONGO_CHAT_STORAGE_COLLECTION)
    date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    query = {
        "status": "Complete",
        "created_at": {"$gte": date},
    }
    total_tokens = 0
    cursor = collection.find(query)
    async for doc in cursor:
        for usage in doc.get("usage", []):
            total_tokens += usage.get("total_tokens", 0)    

    return total_tokens